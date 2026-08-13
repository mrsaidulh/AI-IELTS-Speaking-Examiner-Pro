import unittest
import time
from typing import Dict, Any

from examiner.controller import ExaminerController
from examiner.enums import Part, ExaminerState, ConversationState, ExamMode
from examiner.actions import ExaminerAction
from examiner.validator import ExaminerOutputValidator, ValidationResult
from examiner.questions import PART1_QUESTIONS, PART2_CUE_CARD, PART3_QUESTIONS
from qwen_service import QwenService


class MockQwenService:
    def __init__(self, response_text: str = "That's interesting. Where do you live now?", action_str: str = "ask_next"):
        self.response_text = response_text
        self.action_str = action_str

    def generate_examiner_turn(self, part: int, topic: str, question: str, candidate_answer: str, allowed_action: str):
        class MockLLMResult:
            def __init__(self, text, act):
                self.response = text
                self.action = act
        return MockLLMResult(self.response_text, self.action_str)


class TestLesson51(unittest.TestCase):
    def setUp(self):
        self.session_id = "test_lesson51_session"
        self.controller = ExaminerController(session_id=self.session_id, mode=ExamMode.EXAM)

    def test_controller_initialization_and_question_bank(self):
        """Test controller default setup, question bank retrieval, and state initializers."""
        self.assertEqual(self.controller.part, Part.PART1)
        self.assertEqual(self.controller.state, ExaminerState.INTRODUCTION)
        self.assertEqual(self.controller.conversation_state, ConversationState.IDLE)
        self.assertEqual(self.controller.mode, ExamMode.EXAM)

        q_info = self.controller.get_current_question_info()
        self.assertEqual(q_info["id"], PART1_QUESTIONS[0]["id"])

    def test_dual_state_tracking(self):
        """Test combination of Examination State and Conversation State."""
        self.controller.set_conversation_state(ConversationState.LISTENING)
        self.assertEqual(self.controller.get_combined_state(), "introduction+listening")

        self.controller.start_part2_preparation()
        self.controller.set_conversation_state(ConversationState.THINKING)
        self.assertEqual(self.controller.get_combined_state(), "part2_preparation+thinking")

    def test_exam_vs_practice_mode_configuration(self):
        """Test controller creation in Practice Mode vs Exam Mode."""
        practice_ctrl = ExaminerController(session_id="practice_session", mode=ExamMode.PRACTICE)
        self.assertEqual(practice_ctrl.mode, ExamMode.PRACTICE)
        self.assertEqual(self.controller.mode, ExamMode.EXAM)

    def test_defense_in_depth_output_validator(self):
        """Test ExaminerOutputValidator for empty text, multiple questions, invalid part jumps, and length limits."""
        # 1. Empty text fallback
        res_empty = ExaminerOutputValidator.validate_examiner_output("", 1, "part1", "Where are you from?")
        self.assertFalse(res_empty.is_valid)
        self.assertEqual(res_empty.sanitized_text, "Where are you from?")

        # 2. Multiple questions in single turn
        multi_q = "What is your hometown? Do you like living there? How often do you visit?"
        res_multi = ExaminerOutputValidator.validate_examiner_output(multi_q, 1, "part1")
        self.assertFalse(res_multi.is_valid)
        self.assertEqual(res_multi.sanitized_text, "What is your hometown?")

        # 3. Invalid part jump
        illegal_jump = "Let's move directly to Part 3 to discuss global economic development."
        res_jump = ExaminerOutputValidator.validate_examiner_output(illegal_jump, 1, "part1")
        self.assertFalse(res_jump.is_valid)

        # 4. Valid single question
        valid_q = "What do you enjoy doing in your free time?"
        res_valid = ExaminerOutputValidator.validate_examiner_output(valid_q, 1, "part1")
        self.assertTrue(res_valid.is_valid)
        self.assertEqual(res_valid.sanitized_text, valid_q)

    def test_turn_execution_with_mock_qwen(self):
        """Test process_candidate_turn execution with Qwen generation and state machine advancement."""
        mock_qwen = MockQwenService(
            response_text="Thank you. What do you like about your hometown?",
            action_str="ask_next"
        )

        turn_result = self.controller.process_candidate_turn(
            candidate_answer="I am from Dhaka, Bangladesh.",
            qwen_service=mock_qwen
        )

        self.assertIn("examiner_response", turn_result)
        self.assertEqual(turn_result["action"], ExaminerAction.ASK_NEXT.value)
        self.assertEqual(turn_result["current_part"], Part.PART1.value)
        self.assertIn("combined_state", turn_result)
        self.assertTrue(turn_result["validation"]["is_valid"])
        self.assertEqual(len(self.controller.session.answers), 1)

    def test_override_invalid_llm_action(self):
        """Test that the controller overrides illegal LLM action requests."""
        # LLM requests 'end_test' during Part 1 intro
        mock_qwen_bad = MockQwenService(
            response_text="The test is now completed.",
            action_str="end_test"
        )

        turn_result = self.controller.process_candidate_turn(
            candidate_answer="Hello examiner.",
            qwen_service=mock_qwen_bad
        )

        # Controller must override illegal action 'end_test' with 'ask_next'
        self.assertEqual(turn_result["action"], ExaminerAction.ASK_NEXT.value)


if __name__ == "__main__":
    unittest.main()
