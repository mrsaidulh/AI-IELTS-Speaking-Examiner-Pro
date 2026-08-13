import time
from typing import Dict, Any, List, Optional
from examiner.enums import Part, ExaminerState, ConversationState, ExamMode
from examiner.actions import ExaminerAction
from examiner.questions import PART1_QUESTIONS, PART2_CUE_CARD, PART3_QUESTIONS
from examiner.session import ExaminerSession
from examiner.transitions import get_next_state, is_valid_transition
from examiner.validator import ExaminerOutputValidator, ValidationResult


class ExaminerController:
    """
    Deterministic Examiner Controller for IELTS Speaking test navigation.
    Enforces exam state machine flow (Part 1 -> Part 2 -> Part 3 -> Completed),
    question sequencing, timing rules, and strict validation of LLM examiner actions.
    """
    def __init__(self, session_id: str = "demo-session", mode: ExamMode = ExamMode.EXAM):
        self.session = ExaminerSession(session_id=session_id)
        self.session_id = session_id
        self.part = Part.PART1
        self.state = ExaminerState.INTRODUCTION
        self.conversation_state = ConversationState.IDLE
        self.mode = mode
        
        self.question_index = 0
        self.max_part1_questions = len(PART1_QUESTIONS)
        self.max_part3_questions = len(PART3_QUESTIONS)

        # Part 2 Timers (Server-Authoritative)
        self.part2_prep_time_sec = 60
        self.part2_long_turn_sec = 120
        self.part2_prep_started_at: Optional[float] = None
        self.part2_speaking_started_at: Optional[float] = None

    def set_conversation_state(self, conv_state: ConversationState):
        """Updates current voice conversation state (LISTENING, THINKING, SPEAKING, IDLE)."""
        self.conversation_state = conv_state

    def get_combined_state(self) -> str:
        """
        Returns combined Examination + Conversation state string.
        Example: 'part1+listening', 'part2_preparation+thinking'
        """
        part_str = f"part{self.part.value}" if isinstance(self.part, Part) else str(self.part)
        state_str = self.state.value if isinstance(self.state, ExaminerState) else str(self.state)
        conv_str = self.conversation_state.value if isinstance(self.conversation_state, ConversationState) else str(self.conversation_state)
        return f"{state_str}+{conv_str}"

    def get_current_question_info(self) -> Dict[str, Any]:
        if self.part == Part.PART1:
            idx = min(self.question_index, len(PART1_QUESTIONS) - 1)
            return PART1_QUESTIONS[idx]
        elif self.part == Part.PART2:
            return PART2_CUE_CARD
        elif self.part == Part.PART3:
            idx = min(self.question_index, len(PART3_QUESTIONS) - 1)
            return PART3_QUESTIONS[idx]
        return {"id": "unknown", "topic": "general", "question": "Are you ready?"}

    def determine_allowed_action(self) -> ExaminerAction:
        """
        Determines the strictly permitted action for the current exam state.
        Qwen LLM cannot override this decision.
        """
        if self.state == ExaminerState.INTRODUCTION:
            return ExaminerAction.ASK_NEXT

        if self.part == Part.PART1:
            if self.question_index >= self.max_part1_questions - 1:
                return ExaminerAction.MOVE_PART
            return ExaminerAction.ASK_NEXT

        if self.part == Part.PART2:
            if self.state == ExaminerState.PART2_PREPARATION:
                return ExaminerAction.ASK_NEXT
            elif self.state == ExaminerState.PART2_SPEAKING:
                return ExaminerAction.MOVE_PART
            return ExaminerAction.ASK_NEXT

        if self.part == Part.PART3:
            if self.question_index >= self.max_part3_questions - 1:
                return ExaminerAction.END_TEST
            return ExaminerAction.ASK_NEXT

        return ExaminerAction.END_TEST

    def start_part2_preparation(self):
        """Authoritatively triggers Part 2 preparation timer."""
        self.part = Part.PART2
        self.state = ExaminerState.PART2_PREPARATION
        self.part2_prep_started_at = time.monotonic()

    def get_part2_prep_remaining(self) -> float:
        if self.part2_prep_started_at is None:
            return float(self.part2_prep_time_sec)
        elapsed = time.monotonic() - self.part2_prep_started_at
        return max(0.0, float(self.part2_prep_time_sec) - elapsed)

    def process_candidate_turn(
        self,
        candidate_answer: str,
        qwen_service: Any,
        audio_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a turn in the exam:
        1. Set Conversation State to THINKING
        2. Query Controller for allowed action
        3. Query Qwen for structured response matching allowed action
        4. Level 1/2/3 Defense-in-Depth Validation (Action & Output Validation)
        5. Update deterministic state machine
        6. Record turn record in session history
        7. Set Conversation State to SPEAKING
        """
        start_time = time.time()
        self.set_conversation_state(ConversationState.THINKING)

        q_info = self.get_current_question_info()
        allowed_action = self.determine_allowed_action()

        # Query Qwen LLM for response matching allowed action
        llm_res = qwen_service.generate_examiner_turn(
            part=self.part.value,
            topic=q_info.get("topic", "General"),
            question=q_info.get("question", q_info.get("topic", "")),
            candidate_answer=candidate_answer,
            allowed_action=allowed_action.value
        )

        # 1. Action validation against Controller state machine
        final_action = self.validate_and_apply_action(allowed_action, llm_res.action)

        # 2. Defense-in-Depth Output Validation on generated text
        val_result: ValidationResult = ExaminerOutputValidator.validate_examiner_output(
            text=llm_res.response,
            current_part=self.part.value if isinstance(self.part, Part) else int(self.part),
            current_state=self.state.value if isinstance(self.state, ExaminerState) else str(self.state),
            expected_question=q_info.get("question")
        )

        final_response_text = val_result.sanitized_text

        # Advance state machine
        next_question_info = self.advance_state(final_action)

        turn_duration = round(time.time() - start_time, 3)
        self.set_conversation_state(ConversationState.SPEAKING)

        # Record turn in session history
        turn_record = {
            "part": self.part.value if isinstance(self.part, Part) else self.part,
            "question_index": self.question_index,
            "question_id": q_info.get("id", "q_unknown"),
            "topic": q_info.get("topic", "General"),
            "question": q_info.get("question", q_info.get("topic", "")),
            "candidate_answer": candidate_answer,
            "examiner_response": final_response_text,
            "action": final_action.value,
            "audio_file": audio_file,
            "turn_duration": turn_duration,
            "mode": self.mode.value if isinstance(self.mode, ExamMode) else str(self.mode),
            "validation_passed": val_result.is_valid,
            "timestamp": time.time()
        }
        self.session.answers.append(turn_record)

        return {
            "examiner_response": final_response_text,
            "action": final_action.value,
            "current_part": self.part.value if isinstance(self.part, Part) else self.part,
            "state": self.state.value if isinstance(self.state, ExaminerState) else str(self.state),
            "conversation_state": self.conversation_state.value,
            "combined_state": self.get_combined_state(),
            "next_question": next_question_info,
            "turn_duration": turn_duration,
            "validation": {
                "is_valid": val_result.is_valid,
                "reason": val_result.reason
            }
        }

    def validate_and_apply_action(
        self,
        allowed_action: ExaminerAction,
        requested_action_str: str
    ) -> ExaminerAction:
        if requested_action_str != allowed_action.value:
            print(f"[ExaminerController Guard] Rejected invalid requested action '{requested_action_str}'. Overriding with '{allowed_action.value}'.")
            return allowed_action
        return allowed_action

    def advance_state(self, action: ExaminerAction) -> Optional[Dict[str, Any]]:
        """
        Advances the state machine deterministically based on verified action.
        """
        if self.state == ExaminerState.INTRODUCTION:
            self.state = ExaminerState.PART1
            self.question_index = 0
            return PART1_QUESTIONS[0]

        if action == ExaminerAction.ASK_NEXT:
            self.question_index += 1
            return self.get_current_question_info()

        elif action == ExaminerAction.MOVE_PART:
            if self.part == Part.PART1:
                self.part = Part.PART2
                self.state = ExaminerState.PART2_PREPARATION
                self.question_index = 0
                return PART2_CUE_CARD
            elif self.part == Part.PART2:
                self.part = Part.PART3
                self.state = ExaminerState.PART3
                self.question_index = 0
                return PART3_QUESTIONS[0]

        elif action == ExaminerAction.END_TEST:
            self.state = ExaminerState.COMPLETED
            return None

        return self.get_current_question_info()
