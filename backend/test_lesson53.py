import unittest
import struct
from audio.pipeline import RealtimeAudioPipeline, AudioPipelineMetrics
from audio.buffer import AudioBuffer


class TestLesson53(unittest.TestCase):
    def setUp(self):
        self.sample_rate = 16000
        self.channels = 1
        self.sample_width = 2 # 16-bit PCM = 2 bytes per sample
        self.pipeline = RealtimeAudioPipeline(
            sample_rate=self.sample_rate,
            channels=self.channels,
            sample_width=self.sample_width,
            part_mode="part1"
        )

    def test_audio_format_and_metrics_initialization(self):
        """Test audio pipeline configuration for 16kHz 16-bit Mono PCM and initial metrics."""
        metrics = self.pipeline.get_metrics_dict()
        self.assertEqual(metrics["sample_rate"], 16000)
        self.assertEqual(metrics["channels"], 1)
        self.assertEqual(metrics["sample_width"], 2)
        self.assertEqual(metrics["format"], "pcm_s16le")
        self.assertEqual(metrics["chunks_received"], 0)
        self.assertEqual(metrics["total_bytes"], 0)
        self.assertEqual(metrics["duration_sec"], 0.0)

    def test_audio_chunking_and_buffer_accumulation(self):
        """Test streaming audio chunk processing, buffer accumulation, and duration measurement."""
        # Create a 100ms silent audio chunk: 16000 samples/s * 0.1s * 2 bytes = 3200 bytes
        chunk_100ms = b"\x00\x00" * 1600
        
        # Process chunk 1
        res1 = self.pipeline.process_chunk(pcm_bytes=chunk_100ms)
        self.assertFalse(res1["echo_suppressed"])
        self.assertAlmostEqual(res1["buffered_duration_sec"], 0.1, places=2)

        # Process chunk 2
        res2 = self.pipeline.process_chunk(pcm_bytes=chunk_100ms)
        self.assertAlmostEqual(res2["buffered_duration_sec"], 0.2, places=2)

        # Verify pipeline metrics
        metrics = self.pipeline.get_metrics_dict()
        self.assertEqual(metrics["chunks_received"], 2)
        self.assertEqual(metrics["total_bytes"], 6400)
        self.assertAlmostEqual(metrics["duration_sec"], 0.2, places=2)

    def test_examiner_echo_suppression_guard(self):
        """Test candidate microphone echo suppression guard when examiner is speaking."""
        chunk = b"\x00\x00" * 1600 # 100ms chunk
        
        # Enable examiner speaking flag
        self.pipeline.set_examiner_speaking(True)
        self.assertTrue(self.pipeline.is_examiner_speaking())

        res = self.pipeline.process_chunk(pcm_bytes=chunk)
        self.assertTrue(res["echo_suppressed"])
        self.assertEqual(res["buffered_duration_sec"], 0.0) # Buffer was not updated

        # Disable examiner speaking flag
        self.pipeline.set_examiner_speaking(False)
        self.assertFalse(self.pipeline.is_examiner_speaking())

        res_active = self.pipeline.process_chunk(pcm_bytes=chunk)
        self.assertFalse(res_active["echo_suppressed"])
        self.assertAlmostEqual(res_active["buffered_duration_sec"], 0.1, places=2)

    def test_turn_wav_export_and_reset(self):
        """Test exported 16kHz WAV header and turn buffer reset."""
        # Send 5 chunks (0.5s total audio)
        chunk = b"\x00\x00" * 1600
        for _ in range(5):
            self.pipeline.process_chunk(pcm_bytes=chunk)

        self.assertAlmostEqual(self.pipeline.buffer.get_duration_seconds(), 0.5, places=2)

        # Export WAV bytes
        wav_bytes = self.pipeline.export_turn_wav()
        self.assertTrue(wav_bytes.startswith(b"RIFF"))
        self.assertIn(b"WAVE", wav_bytes[:16])

        # Reset turn
        self.pipeline.reset_turn()
        self.assertEqual(self.pipeline.buffer.get_duration_seconds(), 0.0)
        self.assertEqual(self.pipeline.get_metrics_dict()["chunks_received"], 0)


if __name__ == "__main__":
    unittest.main()
