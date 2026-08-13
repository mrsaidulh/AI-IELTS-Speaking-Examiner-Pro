import unittest
import io
import wave
import struct
from speech.whisper_service import WhisperService, is_cuda_available
from speech.schema import Transcript, TranscriptSegment


def generate_test_wav_bytes(duration_sec: float = 1.5, sample_rate: int = 16000) -> bytes:
    """Helper to generate dummy 16kHz mono WAV bytes for testing."""
    sample_count = int(sample_rate * duration_sec)
    pcm_bytes = struct.pack(f"<{sample_count}h", *[0] * sample_count)
    
    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return wav_io.getvalue()


class TestLesson54(unittest.TestCase):
    def setUp(self):
        self.whisper = WhisperService(model_size="small", device="cpu", compute_type="int8", auto_warmup=False)

    def test_whisper_initialization_and_device_configuration(self):
        """Test Whisper service initialization, device selection, and metadata."""
        self.assertEqual(self.whisper.model_size, "small")
        self.assertIn(self.whisper.device, ["cpu", "cuda"])
        self.assertEqual(self.whisper.default_language, "en")
        self.assertIn(self.whisper.backend_type, ["faster_whisper", "openai_whisper", "mock"])

    def test_whisper_warmup(self):
        """Test Whisper model warm-up inference to initialize GPU/CPU memory."""
        self.assertFalse(self.whisper.is_warmed_up)
        warmup_latency = self.whisper.warmup()
        self.assertTrue(self.whisper.is_warmed_up)
        self.assertGreater(warmup_latency, 0.0)

    def test_explicit_english_language_transcription(self):
        """Test transcription with explicit language ('en') targeting English IELTS domain."""
        audio_bytes = generate_test_wav_bytes(duration_sec=2.0)
        transcript = self.whisper.transcribe(audio_bytes, language="en")
        
        self.assertIsInstance(transcript, Transcript)
        self.assertEqual(transcript.language, "en")
        self.assertFalse(transcript.is_partial)
        self.assertGreater(len(transcript.text), 0)
        self.assertGreaterEqual(transcript.processing_time_sec, 0.0)
        self.assertGreaterEqual(transcript.rtf, 0.0)

    def test_partial_vs_final_transcription_passes(self):
        """Test partial streaming transcription vs authoritative final transcription pass."""
        audio_bytes = generate_test_wav_bytes(duration_sec=1.5)

        # 1. Partial pass (fast beam_size=1)
        partial_tx = self.whisper.transcribe_partial(audio_bytes, language="en")
        self.assertTrue(partial_tx.is_partial)
        self.assertIsInstance(partial_tx.text, str)

        # 2. Final pass (authoritative beam_size=5)
        final_tx = self.whisper.transcribe_final(audio_bytes, language="en")
        self.assertFalse(final_tx.is_partial)
        self.assertIsInstance(final_tx.text, str)

    def test_raw_transcript_preservation(self):
        """Test raw candidate transcript preservation (no silent grammar correction)."""
        audio_bytes = generate_test_wav_bytes(duration_sec=2.5)
        transcript = self.whisper.transcribe(audio_bytes, language="en")
        
        # Verify transcript retains actual raw output and segment metadata
        self.assertIsNotNone(transcript.text)
        self.assertTrue(isinstance(transcript.segments, list))
        for segment in transcript.segments:
            self.assertIsInstance(segment, TranscriptSegment)
            self.assertGreaterEqual(segment.start, 0.0)
            self.assertGreaterEqual(segment.end, segment.start)
            self.assertIsInstance(segment.text, str)

    def test_whisper_benchmark_suite(self):
        """Test Whisper service performance benchmarking across multiple runs."""
        audio_bytes = generate_test_wav_bytes(duration_sec=1.0)
        results = self.whisper.benchmark(audio_bytes, num_runs=3)

        self.assertEqual(results["model_size"], "small")
        self.assertEqual(results["num_runs"], 3)
        self.assertIn("average_latency_sec", results)
        self.assertIn("median_latency_sec", results)
        self.assertIn("p95_latency_sec", results)
        self.assertIn("average_rtf", results)
        self.assertEqual(len(results["latencies_sec"]), 3)


if __name__ == "__main__":
    unittest.main()
