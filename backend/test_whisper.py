import os
import sys
import math
import struct

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from whisper_service import WhisperService
from audio_utils import pcm_to_wav

print("Initializing WhisperService test...")
whisper_service = WhisperService(model_size="small")

# Generate 1 second of 440Hz test tone PCM data
sample_rate = 16000
duration = 1.0
freq = 440.0
num_samples = int(sample_rate * duration)
pcm_chunks = []

for i in range(num_samples):
    value = int(32767.0 * 0.3 * math.sin(2.0 * math.pi * freq * i / sample_rate))
    pcm_chunks.append(struct.pack("<h", value))

test_pcm_bytes = b"".join(pcm_chunks)
test_wav_path = "test_whisper_input.wav"

saved_path = pcm_to_wav(test_pcm_bytes, test_wav_path, sample_rate=16000)

try:
    result = whisper_service.transcribe(saved_path, language="en")
    print("\n--- Whisper Test Result ---")
    print("Transcript:", result["text"])
    print("Language:", result["language"])
    print("Language Probability:", result["language_probability"])
    print("Segments:", result["segments"])
    print("---------------------------\n")
finally:
    if os.path.exists(saved_path):
        os.remove(saved_path)
