import os
import math
import struct
from pcm_to_wav import save_pcm_as_wav

# Generate 1 second of 440Hz sine wave PCM data at 16kHz
sample_rate = 16000
duration = 1.0 # seconds
freq = 440.0 # A4 note

num_samples = int(sample_rate * duration)
pcm_chunks = []

for i in range(num_samples):
    value = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * freq * i / sample_rate))
    pcm_chunks.append(struct.pack("<h", value))

test_pcm_bytes = b"".join(pcm_chunks)
test_output_path = "test_output.wav"

saved_path = save_pcm_as_wav(test_pcm_bytes, test_output_path, sample_rate=16000)

print(f"Generated test WAV at: {saved_path}")
print(f"File exists: {os.path.exists(saved_path)}, File size: {os.path.getsize(saved_path)} bytes")
