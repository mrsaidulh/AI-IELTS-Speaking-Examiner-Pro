import requests

KOKORO_URL = "http://localhost:8880/v1/audio/speech"

def text_to_speech(text, output_file="examiner.mp3"):
    payload = {
        "model": "kokoro",
        "input": text,
        "voice": "af_heart",
        "response_format": "mp3"
    }

    response = requests.post(KOKORO_URL, json=payload, timeout=30)
    response.raise_for_status()

    with open(output_file, "wb") as f:
        f.write(response.content)

    return output_file

if __name__ == "__main__":
    text = """
    Good morning. My name is your IELTS examiner.
    Can you tell me your full name, please?
    """

    try:
        file = text_to_speech(text)
        print(f"Audio saved to: {file}")
    except Exception as e:
        print(f"TTS Error: {e}")
