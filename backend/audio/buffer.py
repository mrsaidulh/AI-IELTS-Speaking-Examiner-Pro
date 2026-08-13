import struct
import io
import wave
from typing import List, Optional


class AudioBuffer:
    """
    Lesson 43 Audio Buffer for Real-Time Microphone PCM Audio Streaming.
    Accumulates raw 16kHz 16-bit Mono PCM audio chunks (pcm_s16le)
    and tracks chunk counts, duration, and PCM to WAV conversions.
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        sample_width: int = 2
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = sample_width  # 2 bytes for 16-bit PCM
        self._buffer = bytearray()
        self._chunk_count = 0

    def append_chunk(self, chunk: bytes) -> None:
        """
        Appends raw PCM bytes chunk to the internal buffer.
        """
        if chunk:
            self._buffer.extend(chunk)
            self._chunk_count += 1

    def append_float_array(self, float_samples: List[float]) -> None:
        """
        Converts array of Float32 audio samples (-1.0 to +1.0) from browser AudioWorklet
        into 16-bit signed PCM little-endian (pcm_s16le) bytes and appends to buffer.
        """
        pcm_bytes = self.float32_to_pcm16(float_samples)
        self.append_chunk(pcm_bytes)

    @staticmethod
    def float32_to_pcm16(float_samples: List[float]) -> bytes:
        """
        Converts Float32 audio samples (-1.0 to 1.0) to 16-bit PCM signed integer bytes.
        """
        pcm_bytes = bytearray()
        for sample in float_samples:
            # Clamp sample between -1.0 and 1.0
            clamped = max(-1.0, min(1.0, sample))
            # Scale to 16-bit integer range [-32768, 32767]
            int_sample = int(clamped * 32767.0) if clamped >= 0 else int(clamped * 32768.0)
            pcm_bytes.extend(struct.pack("<h", int_sample))
        return bytes(pcm_bytes)

    def get_pcm_bytes(self) -> bytes:
        """
        Returns raw accumulated PCM bytes.
        """
        return bytes(self._buffer)

    def get_sample_count(self) -> int:
        """
        Returns total number of audio samples accumulated.
        """
        return len(self._buffer) // (self.sample_width * self.channels)

    def get_duration_seconds(self) -> float:
        """
        Calculates cumulative duration of accumulated audio in seconds.
        """
        bytes_per_second = self.sample_rate * self.sample_width * self.channels
        if bytes_per_second == 0:
            return 0.0
        return len(self._buffer) / bytes_per_second

    def get_chunk_count(self) -> int:
        """
        Returns total number of audio chunks received.
        """
        return self._chunk_count

    def clear(self) -> None:
        """
        Resets the audio buffer and chunk counters.
        """
        self._buffer.clear()
        self._chunk_count = 0

    def export_wav_bytes(self) -> bytes:
        """
        Exports accumulated PCM audio formatted with a standard 16kHz Mono 16-bit WAV header.
        """
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(self.sample_width)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(bytes(self._buffer))
        return wav_io.getvalue()
