import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from examiner.controller import ExaminerController
from qwen_service import QwenService


def test_qwen_controller_loop():
    print("--- Running Qwen + ExaminerController Integration Test (Lesson 39) ---")
    controller = ExaminerController("demo-loop-session")
    qwen_service = QwenService()

    candidate_answers = [
        "I am from Mymensingh, Bangladesh.",
        "I love the calm environment and green parks in my hometown.",
        "Yes, I would definitely love to live there in the future.",
        "I am currently studying Computer Science and Engineering at university.",
        "I enjoy solving complex algorithms and programming challenges."
    ]

    for idx, answer in enumerate(candidate_answers, 1):
        q_info = controller.get_current_question_info()
        print(f"\n[Turn {idx}] Question ({q_info.get('id', 'q')}): {q_info.get('question', q_info.get('topic', ''))}")
        print(f"[Candidate]: {answer}")

        turn_result = controller.process_candidate_turn(
            candidate_answer=answer,
            qwen_service=qwen_service
        )

        print(f"[Examiner Response]: {turn_result['examiner_response']}")
        print(f"[Verified Action]: {turn_result['action']} | Part: {turn_result['current_part']}")

    assert len(controller.session.answers) == len(candidate_answers)
    print("\n✓ Full conversational loop verified! All turns logged with evidence.")


if __name__ == "__main__":
    test_qwen_controller_loop()
