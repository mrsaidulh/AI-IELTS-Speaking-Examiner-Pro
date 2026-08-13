import requests

url = "http://localhost:8880/v1/audio/speech"

payload = {
    "model": "kokoro",
    "input": "What do you like about your hometown?",
    "voice": "af_heart",
    "response_format": "mp3"
}

try:
    response = requests.post(
        url,
        json=payload,
        timeout=15
    )

    print("Status:", response.status_code)

    if response.ok:
        with open("test_question.mp3", "wb") as f:
            f.write(response.content)
        print("Audio saved to test_question.mp3.")
    else:
        print("Error response:", response.text)
except Exception as e:
    print(f"Kokoro test note: {e}")
