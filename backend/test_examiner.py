import os
import sys
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import QWEN_URL, QWEN_MODEL
from qwen_service import QwenService
from prompts.examiner import build_examiner_prompt
from examiner.parser import parse_examiner_response
from examiner.transitions import is_valid_transition, get_next_state


async def main():
    print("--- Running IELTS Examiner Engine Integration Test (Lesson 40) ---")

    qwen = QwenService(base_url=QWEN_URL, model=QWEN_MODEL)

    prompt = build_examiner_prompt(
        part=1,
        topic="Hometown",
        question="What do you like about your hometown?",
        candidate_answer="I like Mymensingh because it is relatively quiet and the environment is clean.",
        allowed_action="ASK_NEXT"
    )

    print("\n[Generated Examiner Prompt]:")
    print(prompt)

    # Generate turn via async method
    examiner_res = await qwen.generate_examiner_turn_async(
        part=1,
        topic="Hometown",
        question="What do you like about your hometown?",
        candidate_answer="I like Mymensingh because it is relatively quiet and the environment is clean.",
        allowed_action="ASK_NEXT"
    )

    print(f"\n[Parsed Examiner Response]: {examiner_res.response}")
    print(f"[Validated Examiner Action]: {examiner_res.action}")

    # Verify transition matrix
    current_state = "part1"
    valid = is_valid_transition(current_state, examiner_res.action)
    next_st = get_next_state(current_state, examiner_res.action)

    assert valid is True
    print(f"✓ Action '{examiner_res.action}' is valid for state '{current_state}'. Next State: '{next_st}'.")
    print("✓ IELTS Examiner prompt & parser validation verified.")


if __name__ == "__main__":
    asyncio.run(main())
