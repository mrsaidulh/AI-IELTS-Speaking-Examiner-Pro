import json
import re
from typing import Optional, Dict, Any
from examiner.schema import ExaminerResponse


def extract_json_string(raw_text: str) -> str:
    """
    Strips markdown code blocks (```json ... ```) or extra leading/trailing whitespace
    to isolate raw JSON string.
    """
    clean_text = raw_text.strip()
    if clean_text.startswith("```"):
        lines = clean_text.splitlines()
        # Filter out ```json and ``` lines
        content_lines = [line for line in lines if not line.strip().startswith("```")]
        clean_text = "\n".join(content_lines).strip()
    
    # Regex fallback if text is wrapped in surrounding chatter
    match = re.search(r"\{.*\}", clean_text, re.DOTALL)
    if match:
        return match.group(0)
    return clean_text


def parse_examiner_response(raw_response: str) -> ExaminerResponse:
    """
    Parses raw LLM string output into a validated Pydantic ExaminerResponse model.
    Raises ValueError on invalid JSON or missing fields to trigger fallback handling.
    """
    if not raw_response or not raw_response.strip():
        raise ValueError("Empty response received from LLM")

    json_str = extract_json_string(raw_response)
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as err:
        raise ValueError(f"Failed to parse LLM JSON output: {err}")

    if not isinstance(data, dict):
        raise ValueError("LLM output is not a valid JSON object")

    return ExaminerResponse(**data)
