import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from examiner.controller import ExaminerController
from examiner.enums import Part, ExaminerState
from examiner.actions import ExaminerAction


def test_controller_state_transitions():
    print("--- Running ExaminerController Unit Tests (Lesson 38) ---")
    controller = ExaminerController("test-session")

    # Initial state check
    assert controller.part == Part.PART1
    assert controller.state == ExaminerState.INTRODUCTION
    print("✓ Initial state: Part 1, INTRODUCTION")

    # Move through Part 1 questions
    for i in range(len(controller.max_part1_questions if hasattr(controller, 'max_part1_questions') else [1, 2, 3, 4, 5])):
        action = controller.determine_allowed_action()
        print(f"Part 1 Question {controller.question_index + 1}: Action = {action.value}")
        controller.advance_state(action)

    # Check transition to Part 2
    assert controller.part == Part.PART2
    assert controller.state == ExaminerState.PART2_PREPARATION
    print("✓ Transitioned to Part 2 (PART2_PREPARATION)")

    # Move from Part 2 to Part 3
    action = controller.determine_allowed_action()
    controller.advance_state(action)
    assert controller.part == Part.PART3
    assert controller.state == ExaminerState.PART3
    print("✓ Transitioned to Part 3 (PART3)")

    # Complete Part 3
    for _ in range(3):
        action = controller.determine_allowed_action()
        controller.advance_state(action)

    assert controller.state == ExaminerState.COMPLETED
    print("✓ Test completed successfully (COMPLETED state reached).")


if __name__ == "__main__":
    test_controller_state_transitions()
