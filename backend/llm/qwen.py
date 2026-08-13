import json
import urllib.request
import urllib.error
from config import QWEN_URL, QWEN_MODEL


class QwenService:

    def __init__(self, url=QWEN_URL, model=QWEN_MODEL, model_name=None, mock_mode=False):
        self.url = url
        self.model = model_name or model
        self.mock_mode = mock_mode


    def generate(self, prompt, system_prompt=None):
        if self.mock_mode:
            return json.dumps({
                "action": "ASK_QUESTION",
                "text": "What do you like most about your hometown?"
            })

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if system_prompt:
            payload["system"] = system_prompt

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.url}/api/generate",
            data=req_data,
            headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                res_json = json.loads(resp.read().decode("utf-8"))
                return res_json.get("response", "").strip()
        except Exception as e:
            print(f"QwenService connection fallback ({e}).")
            return json.dumps({
                "action": "ASK_QUESTION",
                "text": "Thank you. What do you like most about your hometown?"
            })

    def generate_response(self, prompt, system_prompt=None):
        """Generates structured JSON response for Examiner Controller."""
        return self.generate(prompt, system_prompt)


    def generate_evaluation(self, question, answer, duration):
        prompt = f"""
Evaluate the following IELTS answer:
Question: "{question}"
Answer: "{answer}"
Duration: {duration} seconds

Return JSON:
{{
  "relevance": 0.9,
  "communication_quality": 0.85,
  "notes": "Good task response."
}}
"""
        raw_res = self.generate(prompt)
        try:
            return json.loads(raw_res)
        except Exception:
            return {
                "relevance": 0.9,
                "communication_quality": 0.85,
                "notes": "Relevant answer."
            }
