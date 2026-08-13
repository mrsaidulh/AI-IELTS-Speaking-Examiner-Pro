import requests

url = "http://localhost:8880/v1/audio/speech"

payload = {
    "model": "kokoro",
    "input": "Good morning. Can you tell me where you are from?",
    "voice": "af_heart",
    "response_format": "mp3"
}

try:
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()

    with open("examiner.mp3", "wb") as f:
        f.write(response.content)

    print("Audio generated successfully.")
    print("Saved as examiner.mp3")
except Exception as e:
    print(f"Kokoro test note: Could not reach {url} directly ({e}). Ensure Kokoro container is running on port 8880.")
