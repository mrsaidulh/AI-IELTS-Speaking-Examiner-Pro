import os
import sys
import json
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from examiner.actions import ExaminerAction
from examiner.schema import ExaminerResponse
from examiner.parser import parse_examiner_response
from examiner.transitions import validate_transition, is_valid_transition, TRANSITIONS
from qwen_service import QwenService


def test_level1_prompt_and_schema():
    print("--- Test 1: Level 2 Pydantic Schema + ExaminerAction Enum ---")
    
    # 1. Valid action string -> converted to Enum
    valid_raw = json.dumps({"response": "What do you like about your hometown?", "action": "ASK_NEXT"})
    parsed = parse_examiner_response(valid_raw)
    assert isinstance(parsed.action, ExaminerAction)
    assert parsed.action == ExaminerAction.ASK_NEXT
    print("✓ Valid JSON with 'ASK_NEXT' successfully validated as ExaminerAction.ASK_NEXT.")

    # 2. Invalid action string -> rejected by Level 2 schema validation
    invalid_action_raw = json.dumps({"response": "Let's launch to space.", "action": "FLY_TO_MOON"})
    try:
        parse_examiner_response(invalid_action_raw)
        assert False, "Should have raised ValueError due to invalid action Enum!"
    except ValueError as err:
        print(f"✓ Invalid action 'FLY_TO_MOON' correctly rejected by Level 2 schema validation: {err}")


def test_level3_transition_validation():
    print("\n--- Test 2: Level 3 State Transition Matrix Validation ---")

    # Valid transition: part1 -> ASK_NEXT
    assert is_valid_transition("part1", "ASK_NEXT") is True
    next_st = validate_transition("part1", "ASK_NEXT")
    assert next_st == "part1"
    print("✓ State 'part1' + Action 'ASK_NEXT' is valid transition -> Next State: 'part1'")

    # Valid transition: part1 -> MOVE_PART
    assert is_valid_transition("part1", "MOVE_PART") is True
    next_st_move = validate_transition("part1", "MOVE_PART")
    assert next_st_move == "part2_preparation"
    print("✓ State 'part1' + Action 'MOVE_PART' is valid transition -> Next State: 'part2_preparation'")

    # Invalid transition: part1 -> END_TEST
    assert is_valid_transition("part1", "END_TEST") is False
    try:
        validate_transition("part1", "END_TEST")
        assert False, "Should have raised ValueError for invalid state transition!"
    except ValueError as err:
        print(f"✓ Invalid transition 'END_TEST' from state 'part1' correctly rejected by Level 3 Guard: {err}")


async def test_qwen_streaming_and_fallback():
    print("\n--- Test 3: Streaming JSON Assembly & Controller Fallback ---")

    qwen = QwenService(base_url="http://localhost:11434", model="qwen2.5:7b")

    # Simulate streaming JSON chunks (Strategy A: assemble full text before parsing)
    chunks = [
        "{\n",
        '  "response": "That is very interesting.',
        ' What else do you like about it?",\n',
        '  "action": "ASK_NEXT"\n',
        "}"
    ]
    assembled_stream = "".join(chunks)
    parsed_stream = parse_examiner_response(assembled_stream)
    assert parsed_stream.action == ExaminerAction.ASK_NEXT
    print(f"✓ Strategy A JSON streaming chunk assembly verified. Response: '{parsed_stream.response}'")

    # Test Fallback when Ollama API is offline / unparseable
    fallback_res = qwen.generate_examiner_turn(
        part=1,
        topic="Hometown",
        question="What do you like about your hometown?",
        candidate_answer="I like the peaceful nature.",
        allowed_action="ASK_NEXT",
        current_state="part1"
    )
    assert isinstance(fallback_res.action, ExaminerAction)
    assert len(fallback_res.response) > 0
    print(f"✓ Fallback architecture verified: {fallback_res.response} [Action: {fallback_res.action}]")


async def main():
    print("===============================================================")
    print("   Running Lesson 41 Unit & Integration Test Suite            ")
    print("===============================================================")
    test_level1_prompt_and_schema()
    test_level3_transition_validation()
    await test_qwen_streaming_and_fallback()
    print("\n✓ ALL LESSON 41 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(main())
