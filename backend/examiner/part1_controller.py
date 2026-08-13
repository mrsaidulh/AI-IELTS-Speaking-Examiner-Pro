import uuid
import re
from examiner.session import IELTSSession, SessionState
from examiner.manager import QuestionManager
from examiner.state_machine import Part1State
from examiner.part1 import INTRODUCTION, PART_1_CONFIG


class Part1Controller:

    def __init__(self, question_manager=None, evaluator=None, candidate_name="Candidate"):
        self.session_id = str(uuid.uuid4())
        self.session = IELTSSession(candidate_name=candidate_name)
        self.session.state = SessionState.PART_1
        self.question_manager = question_manager or QuestionManager()
        self.evaluator = evaluator
        self.state = Part1State.INTRODUCTION
        self.intro_index = 0
        self.question_count = 0
        self.answer_count = 0
        self.current_question = None
        self.current_topic = None
        self.used_questions = set()
        self.history = []
        self.evaluations = []
        self.max_answer_seconds = PART_1_CONFIG.get("max_answer_seconds", 60)
        self.silence_timeout_seconds = PART_1_CONFIG.get("silence_timeout_seconds", 10)

    def get_next_intro_step(self):
        if self.intro_index < len(INTRODUCTION):
            text = INTRODUCTION[self.intro_index]
            self.intro_index += 1
            self.state = Part1State.INTRODUCTION
            self.history.append({"role": "examiner", "text": text})
            return text
        return None

    def start_topics(self):
        self.state = Part1State.TOPIC_START

    def next_question(self):
        q_data = self.question_manager.get_next_question()
        if not q_data:
            self.state = Part1State.COMPLETED
            self.session.state = SessionState.PART_2
            return None

        previous_topic = self.current_topic
        self.current_topic = q_data["topic"]
        self.current_question = q_data["question"]
        self.used_questions.add(self.current_question)

        self.session.set_question(self.current_question)
        self.question_count += 1
        
        if previous_topic != self.current_topic:
            self.state = Part1State.TOPIC_START
        else:
            self.state = Part1State.ASKING

        self.history.append({
            "role": "examiner",
            "text": self.current_question
        })

        return {
            "part": "part1",
            "topic": self.current_topic,
            "question": self.current_question,
            "question_number": self.question_count,
            "topic_changed": previous_topic != self.current_topic
        }

    def start_listening(self):
        self.state = Part1State.LISTENING

    def classify_response_intent(self, transcript: str) -> str:
        """Classify candidate response intent (clarification, short answer, valid answer, no answer)."""
        if not transcript or transcript.strip() == "[No speech detected]":
            return "no_answer"
        
        low = transcript.lower().strip()
        clarification_patterns = [
            r"what do you mean", r"could you repeat", r"can you repeat", 
            r"pardon", r"what does .* mean", r"i don't understand the question",
            r"could you rephrase"
        ]
        for pat in clarification_patterns:
            if re.search(pat, low):
                return "clarification_request"
        
        return "valid_answer"

    def process_answer(self, transcript: str, duration: float, segments: list = None):
        self.state = Part1State.EVALUATING
        self.answer_count += 1

        self.history.append({
            "role": "candidate",
            "text": transcript
        })

        rec = self.session.record_answer(transcript, duration)
        intent = self.classify_response_intent(transcript)

        evaluation_result = None
        # Evaluate silently server-side if evaluator available and valid answer
        if self.evaluator and intent != "clarification_request":
            try:
                evaluation_result = self.evaluator.evaluate_answer(
                    question=self.current_question or "General Question",
                    answer=transcript,
                    duration=duration,
                    segments=segments
                )
                self.evaluations.append({
                    "question_number": self.question_count,
                    "question": self.current_question,
                    "transcript": transcript,
                    "duration": duration,
                    "evaluation": evaluation_result
                })
            except Exception as e:
                print(f"Silent evaluation exception: {e}")

        return {
            "record": rec,
            "intent": intent,
            "evaluation": evaluation_result
        }

    def handle_no_answer(self):
        self.state = Part1State.EVALUATING
        return self.process_answer("[No speech detected]", 0.0)

    def is_completed(self):
        return self.state == Part1State.COMPLETED

    def build_event(self, event_type: str, payload: dict = None):
        event = {
            "type": event_type,
            "session_id": self.session_id,
            "part": "part1",
            "state": self.state.value if isinstance(self.state, Part1State) else str(self.state),
            "topic": self.current_topic,
            "question_number": self.question_count
        }
        if payload:
            event.update(payload)
        return event

