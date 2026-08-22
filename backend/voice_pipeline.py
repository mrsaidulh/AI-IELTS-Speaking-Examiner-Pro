import os
import requests
import tempfile

from faster_whisper import WhisperModel

# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/chat"
KOKORO_URL = "http://localhost:8880/v1/audio/speech"
LLM_MODEL = "qwen2.5:7b-instruct"

# ============================================================
# WHISPER
# ============================================================

whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        whisper_model = WhisperModel(
            "small",
            device="cpu",
            compute_type="int8"
        )
    return whisper_model

# ============================================================
# IELTS EXAMINER PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are an IELTS Speaking examiner.

Conduct a realistic IELTS Speaking examination.

Rules:

1. Ask only one question at a time.
2. Do not correct the candidate during the test.
3. Do not teach vocabulary during the test.
4. Do not give feedback during the test.
5. Keep questions natural and concise.
6. Ask appropriate follow-up questions.
7. Use the candidate's previous answers when appropriate.
8. Do not unnecessarily repeat questions.
9. Maintain a professional examiner style.
10. Do not praise the candidate excessively.
11. Do not provide model answers.
12. Respond only as the examiner.
"""

# ============================================================
# CONVERSATION MEMORY
# ============================================================

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]

# ============================================================
# SPEECH TO TEXT
# ============================================================

def transcribe_audio(audio_file):
    model = get_whisper_model()
    segments, info = model.transcribe(
        audio_file,
        beam_size=5
    )

    text = " ".join(
        segment.text.strip()
        for segment in segments
    )

    return text

# ============================================================
# OLLAMA
# ============================================================

def ask_examiner(candidate_text):
    messages.append({
        "role": "user",
        "content": candidate_text
    })

    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "stream": False
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=30
    )

    response.raise_for_status()
    data = response.json()
    examiner_text = data["message"]["content"]

    messages.append({
        "role": "assistant",
        "content": examiner_text
    })

    return examiner_text

# ============================================================
# TEXT TO SPEECH
# ============================================================

def text_to_speech(text, output_file):
    payload = {
        "model": "kokoro",
        "input": text,
        "voice": "af_heart",
        "response_format": "mp3"
    }

    response = requests.post(
        KOKORO_URL,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    with open(output_file, "wb") as f:
        f.write(response.content)

    return output_file

# ============================================================
# COMPLETE PIPELINE
# ============================================================

def process_audio(audio_file):
    print("\n[1] Transcribing...")
    candidate_text = transcribe_audio(audio_file)
    print("Candidate:", candidate_text)

    print("\n[2] Asking Qwen...")
    try:
        examiner_text = ask_examiner(candidate_text)
    except Exception as err:
        print(f"Ollama/Qwen error: {err}")
        examiner_text = "Thank you. Could you tell me more about where you live?"

    print("Examiner:", examiner_text)

    print("\n[3] Generating voice...")
    output_file = "examiner.mp3"

    try:
        text_to_speech(examiner_text, output_file)
        print("\nAudio generated:", output_file)
    except Exception as err:
        print(f"Kokoro TTS error: {err}")

    return {
        "candidate_text": candidate_text,
        "examiner_text": examiner_text,
        "audio_file": output_file
    }
