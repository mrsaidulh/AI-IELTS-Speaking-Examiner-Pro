import requests

url = "http://localhost:11434/api/chat"

payload = {
    "model": "qwen3:8b",
    "messages": [
        {
            "role": "user",
            "content": "Ask me one simple IELTS Speaking Part 1 question."
        }
    ],
    "stream": False
}

try:
    response = requests.post(url, json=payload, timeout=10)
    print(response.json())
except Exception as e:
    print(f"Ollama test note: Could not reach {url} directly ({e}). Ensure Ollama is running locally.")
