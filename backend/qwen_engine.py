import requests
import json
from config import (
    QWEN_URL,
    QWEN_MODEL
)


class QwenEngine:

    def __init__(self):
        self.url = QWEN_URL.rstrip("/")
        self.model = QWEN_MODEL or "qwen2.5:7b"
        self._checked = False

    def _discover_model(self):
        if self._checked:
            return
        try:
            r = requests.get(f"{self.url}/api/tags", timeout=1.5)
            if r.status_code == 200:
                models = [m.get("name") for m in r.json().get("models", []) if m.get("name")]
                if models and self.model not in models:
                    qwen_match = next((m for m in models if "qwen" in m.lower()), models[0])
                    self.model = qwen_match
            self._checked = True
        except Exception:
            self._checked = True

    def generate(
        self,
        prompt
    ):
        self._discover_model()
        try:
            response = requests.post(
                f"{self.url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except Exception:
            return "Thank you. Let's continue with the next IELTS question."
