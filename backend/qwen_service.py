import json
import re
import sys
import os
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, AsyncGenerator, Generator

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import QWEN_URL, QWEN_MODEL
from prompts.examiner import build_examiner_prompt
from examiner.actions import ExaminerAction
from examiner.schema import ExaminerResponse
from examiner.parser import parse_examiner_response
from examiner.transitions import validate_transition, is_valid_transition

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False


class QwenService:
    """
    Qwen LLM Service connecting to local Ollama API (http://localhost:11434).
    Supports structured evaluation mode (Pydantic + state transitions) and streaming mode,
    low temperature (0.3), retry logic, and deterministic controller fallbacks.
    """
    def __init__(self, base_url: str = QWEN_URL, model: str = QWEN_MODEL, temperature: float = 0.3):
        self.base_url = base_url.rstrip('/')
        self.url = self.base_url
        self.model = model
        self.temperature = temperature

    def generate(self, prompt: str, system_prompt: Optional[str] = None, stream: bool = False) -> str:
        """
        Synchronously sends prompt to local Ollama API (/api/generate).
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": self.temperature
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=req_data,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                if stream:
                    # Collect streaming tokens into full string (Strategy A: Assemble complete JSON before parsing)
                    full_text = ""
                    for line in resp:
                        if line:
                            data = json.loads(line.decode("utf-8"))
                            full_text += data.get("response", "")
                            if data.get("done", False):
                                break
                    return full_text.strip()
                else:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    return res_json.get("response", "").strip()
        except Exception as e:
            print(f"[QwenService Sync] Ollama API unreachable or timeout ({e}). Using fallback.")
            return ""

    async def generate_async(self, prompt: str, system_prompt: Optional[str] = None, stream: bool = False) -> str:
        """
        Asynchronously sends prompt to local Ollama API (/api/generate) using httpx.
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": self.temperature
            }
        }
        if system_prompt:
            payload["system"] = system_prompt

        if HTTPX_AVAILABLE:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    if stream:
                        full_text = ""
                        async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                            async for line in response.aiter_lines():
                                if line:
                                    data = json.loads(line)
                                    full_text += data.get("response", "")
                                    if data.get("done", False):
                                        break
                        return full_text.strip()
                    else:
                        resp = await client.post(f"{self.base_url}/api/generate", json=payload)
                        if resp.status_code == 200:
                            data = resp.json()
                            return data.get("response", "").strip()
            except Exception as err:
                print(f"[QwenService Async] httpx call failed ({err}).")

        # Fallback to sync call if httpx fails or not installed
        return self.generate(prompt, system_prompt, stream=stream)

    async def generate_stream_tokens_async(self, prompt: str) -> AsyncGenerator[str, None]:
        """
        Async token generator for streaming text chunks from Ollama API.
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": self.temperature}
        }
        if HTTPX_AVAILABLE:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    async with client.stream("POST", f"{self.base_url}/api/generate", json=payload) as response:
                        async for line in response.aiter_lines():
                            if line:
                                data = json.loads(line)
                                token = data.get("response", "")
                                if token:
                                    yield token
                                if data.get("done", False):
                                    break
                return
            except Exception as e:
                print(f"[QwenService Stream] Streaming error: {e}")

        # Fallback
        res = self.generate(prompt)
        yield res

    def generate_examiner_turn(
        self,
        part: int,
        topic: str,
        question: str,
        candidate_answer: str,
        allowed_action: str,
        current_state: str = "part1",
        max_retries: int = 1
    ) -> ExaminerResponse:
        """
        Structured Mode with 3 Validation Levels & Retry Fallback:
        Level 1: Prompt Builder
        Level 2: Pydantic Schema Validation (ExaminerResponse)
        Level 3: Controller State Transition Matrix Validation
        """
        prompt = build_examiner_prompt(
            part=part,
            topic=topic,
            question=question,
            candidate_answer=candidate_answer,
            allowed_action=allowed_action
        )

        fallback_action = ExaminerAction._missing_(allowed_action) or ExaminerAction.ASK_NEXT
        fallback_text = self._get_fallback_response(part, allowed_action)

        for attempt in range(max_retries + 1):
            raw_res = self.generate(prompt)
            if not raw_res:
                continue

            try:
                # Level 2: Pydantic Schema
                parsed = parse_examiner_response(raw_res)

                # Level 3: State Transition Check
                if not is_valid_transition(current_state, parsed.action):
                    print(f"[QwenService Guard] Invalid state transition '{parsed.action}' from '{current_state}'. Overriding action with '{allowed_action}'.")
                    parsed.action = fallback_action

                return parsed
            except Exception as err:
                print(f"[QwenService Validation Attempt {attempt+1}/{max_retries+1} Failed]: {err}")

        print("[QwenService Fallback] Reached max retries. Engaging deterministic controller fallback.")
        return ExaminerResponse(response=fallback_text, action=fallback_action)

    async def generate_examiner_turn_async(
        self,
        part: int,
        topic: str,
        question: str,
        candidate_answer: str,
        allowed_action: str,
        current_state: str = "part1",
        max_retries: int = 1
    ) -> ExaminerResponse:
        """
        Async Structured Turn Generator with 3 Validation Levels & Retry Fallback.
        """
        prompt = build_examiner_prompt(
            part=part,
            topic=topic,
            question=question,
            candidate_answer=candidate_answer,
            allowed_action=allowed_action
        )

        fallback_action = ExaminerAction._missing_(allowed_action) or ExaminerAction.ASK_NEXT
        fallback_text = self._get_fallback_response(part, allowed_action)

        for attempt in range(max_retries + 1):
            raw_res = await self.generate_async(prompt)
            if not raw_res:
                continue

            try:
                # Level 2: Pydantic Schema
                parsed = parse_examiner_response(raw_res)

                # Level 3: State Transition Check
                if not is_valid_transition(current_state, parsed.action):
                    print(f"[QwenService Guard Async] Invalid state transition '{parsed.action}' from '{current_state}'. Overriding action with '{allowed_action}'.")
                    parsed.action = fallback_action

                return parsed
            except Exception as err:
                print(f"[QwenService Async Attempt {attempt+1}/{max_retries+1} Failed]: {err}")

        print("[QwenService Async Fallback] Reached max retries. Engaging deterministic controller fallback.")
        return ExaminerResponse(response=fallback_text, action=fallback_action)

    def _get_fallback_response(self, part: int, allowed_action: str) -> str:
        act_str = allowed_action.lower()
        if "move" in act_str:
            return f"Thank you. Now let's move on to Part {part + 1}."
        if "end" in act_str or "completed" in act_str:
            return "Thank you very much. That is the end of the IELTS Speaking test."
        if "repeat" in act_str:
            return "Let me repeat the question for you."
        return "Thank you. Let's move on to the next question."


__all__ = ["QwenService"]
