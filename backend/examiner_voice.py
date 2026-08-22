import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
KOKORO_URL = "http://localhost:8880/v1/audio/speech"

MODEL = "qwen2.5:7b-instruct"

SYSTEM_PROMPT = """
You are an IELTS Speaking examiner.

Conduct a realistic IELTS Speaking test.

Rules:

1. Ask only one question at a time.
2. Do not correct the candidate during the test.
3. Do not teach vocabulary during the test.
4. Keep Part 1 questions natural and concise.
5. Ask relevant follow-up questions.
6. Use previous answers when appropriate.
7. Do not unnecessarily repeat questions.
8. Maintain a professional examiner style.
9. Do not evaluate the candidate unless explicitly requested.
10. Respond only as the IELTS examiner.
"""

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]

def ask_ollama(candidate_text):
    messages.append({
        "role": "user",
        "content": candidate_text
    })

    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()
    examiner_text = data["message"]["content"]

    messages.append({
        "role": "assistant",
        "content": examiner_text
    })

    return examiner_text

def speak(text, filename="examiner.mp3"):
    payload = {
        "model": "kokoro",
        "input": text,
        "voice": "af_heart",
        "response_format": "mp3"
    }

    response = requests.post(KOKORO_URL, json=payload, timeout=30)
    response.raise_for_status()

    with open(filename, "wb") as f:
        f.write(response.content)

    return filename

if __name__ == "__main__":
    print("================================")
    print(" LOCAL IELTS VOICE EXAMINER")
    print("================================")

    while True:
        try:
            candidate = input("\nCandidate: ")
            if candidate.lower() in ["exit", "quit"]:
                break

            examiner = ask_ollama(candidate)
            print("\nExaminer:")
            print(examiner)

            try:
                audio_file = speak(examiner)
                print(f"\nAudio generated: {audio_file}")
            except Exception as err:
                print(f"\nAudio synthesis skipped/error: {err}")
        except KeyboardInterrupt:
            break
