import os

class Settings:
    SAMPLE_RATE = 16000
    VAD_SILENCE_TIMEOUT = 1.5
    VAD_MIN_SPEECH_DURATION = 0.3
    VAD_PRE_SPEECH_PADDING = 0.2
    VAD_POST_SPEECH_PADDING = 0.2
    MAX_ANSWER_DURATION = 60
    WHISPER_MODEL = "small"
    KOKORO_URL = os.getenv("KOKORO_URL", "http://localhost:8880")
    QWEN_URL = os.getenv("QWEN_URL", "http://localhost:11434")
    QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen3:8b")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ielts.db")

    PART_CONFIG = {
        "part1": {"max_answer": 30, "silence_timeout": 1.5},
        "part2": {"max_answer": 120, "silence_timeout": 2.0},
        "part3": {"max_answer": 90, "silence_timeout": 1.8}
    }

settings = Settings()

QWEN_URL = settings.QWEN_URL
QWEN_MODEL = settings.QWEN_MODEL
KOKORO_URL = settings.KOKORO_URL
DATABASE_URL = settings.DATABASE_URL
