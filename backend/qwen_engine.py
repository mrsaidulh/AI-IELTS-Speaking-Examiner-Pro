import requests

from config import (
    QWEN_URL,
    QWEN_MODEL
)


class QwenEngine:

    def generate(
        self,
        prompt
    ):
        response = requests.post(
            f"{QWEN_URL}/api/generate",
            json={
                "model": QWEN_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        return data["response"].strip()
