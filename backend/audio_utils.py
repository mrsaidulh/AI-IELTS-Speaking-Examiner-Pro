import wave
import os

def pcm_to_wav(pcm_data: bytes, output_path: str, sample_rate: int = 16000, channels: int = 1, sample_width: int = 2) -> str:
    """
    Converts raw 16-bit PCM audio bytes directly into a standard 16kHz mono WAV file.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with wave.open(output_path, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(sample_width)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm_data)
    return output_path
