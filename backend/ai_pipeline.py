import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "qwen3:8b"

SYSTEM_PROMPT = """
You are an IELTS Speaking examiner.

Conduct a realistic IELTS Speaking test.

Ask one question at a time.

Do not correct the candidate during the test.

Do not give feedback during the test.

Use previous answers to ask natural follow-up questions.

Keep the examiner's responses concise.

Respond only as the IELTS examiner.
"""

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]

def ask_ai(candidate_text):
    messages.append({
        "role": "user",
        "content": candidate_text
    })

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        answer = data["message"]["content"]
        messages.append({
            "role": "assistant",
            "content": answer
        })
        return answer
    except Exception as e:
        return f"Examiner pipeline error: {e}"

if __name__ == "__main__":
    print("================================")
    print(" LOCAL IELTS SPEAKING AI")
    print("================================")
    print("Type 'exit' to stop.\n")

    while True:
        try:
            candidate = input("Candidate: ")
            if candidate.lower() in ["exit", "quit"]:
                break
            examiner = ask_ai(candidate)
            print("\nExaminer:", examiner)
            print()
        except KeyboardInterrupt:
            break
