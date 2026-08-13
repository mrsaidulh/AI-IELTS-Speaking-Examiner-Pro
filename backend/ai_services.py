from whisper_engine import WhisperEngine
from qwen_engine import QwenEngine
from kokoro_engine import KokoroEngine

# Centralized singleton AI service instances loaded once for backend initialization
whisper_engine = WhisperEngine("small")
qwen_engine = QwenEngine()
kokoro_engine = KokoroEngine()

