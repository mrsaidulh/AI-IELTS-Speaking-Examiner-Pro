import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
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
6. Use the candidate's previous answers when appropriate.
7. Do not unnecessarily repeat questions.
8. Maintain a professional examiner style.
9. Do not evaluate the candidate unless explicitly requested.
10. Respond only as the examiner.
"""

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]

def ask_examiner(candidate_answer):
    messages.append({
        "role": "user",
        "content": candidate_answer
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
        examiner_response = data["message"]["content"]
        messages.append({
            "role": "assistant",
            "content": examiner_response
        })
        return examiner_response
    except Exception as e:
        return f"Examiner connection error: {e}"

if __name__ == "__main__":
    print("IELTS Speaking AI Simulator (Lesson 3 CLI)")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            answer = input("Candidate: ")
            if answer.lower() in ["exit", "quit"]:
                break
            response = ask_examiner(answer)
            print("\nExaminer:", response)
            print()
        except KeyboardInterrupt:
            break
