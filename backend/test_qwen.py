import os
import sys
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import QWEN_URL, QWEN_MODEL
from qwen_service import QwenService


async def main():
    print(f"--- Running Qwen + Ollama Connection Test (Lesson 40) ---")
    print(f"Connecting to Ollama at {QWEN_URL} using model '{QWEN_MODEL}'...")

    qwen = QwenService(base_url=QWEN_URL, model=QWEN_MODEL)

    prompt = "Say hello in one sentence as an official IELTS Speaking examiner."
    print(f"\n[Prompt]: {prompt}")

    # Test sync generation
    sync_response = qwen.generate(prompt)
    print(f"[Sync Response]: {sync_response if sync_response else '(Offline/Fallback active)'}")

    # Test async generation
    async_response = await qwen.generate_async(prompt)
    print(f"[Async Response]: {async_response if async_response else '(Offline/Fallback active)'}")

    print("✓ QwenService Ollama API interface test completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
