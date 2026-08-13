from fastapi import FastAPI, UploadFile, File
from faster_whisper import WhisperModel
import tempfile
import os

app = FastAPI(
    title="IELTS AI Speech-to-Text API",
    description="Local Speech-to-Text using faster-whisper",
    version="0.2.0"
)

# Lazy loading or startup initialization of WhisperModel
model = None

def get_whisper_model():
    global model
    if model is None:
        model = WhisperModel(
            "small",
            device="cpu",
            compute_type="int8"
        )
    return model

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "IELTS AI Speech-to-Text"
    }

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1] or ".wav"

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as temp:
        content = await file.read()
        temp.write(content)
        audio_path = temp.name

    try:

        whisper = get_whisper_model()
        segments, info = whisper.transcribe(
            audio_path,
            beam_size=5
        )

        text = " ".join(
            segment.text.strip()
            for segment in segments
        )

        return {
            "language": info.language,
            "language_probability": float(info.language_probability),
            "text": text
        }

    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)
