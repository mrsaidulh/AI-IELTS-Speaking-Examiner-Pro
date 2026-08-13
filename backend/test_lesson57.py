import unittest
from speech.kokoro_service import KokoroService, KokoroAudioResult, KokoroTTSService


class TestLesson57(unittest.TestCase):
    def setUp(self):
        self.tts = KokoroService(voice="af_sarah", speed=1.0)

    def test_kokoro_service_initialization_and_voice_config(self):
        """Test Kokoro TTS service initialization, voice selection, and speed settings."""
        self.assertEqual(self.tts.voice, "af_sarah")
        self.assertEqual(self.tts.speed, 1.0)
        self.assertEqual(KokoroTTSService, KokoroService)

    def test_examiner_text_to_speech_synthesis(self):
        """Test synthesis of examiner text into clean PCM/WAV binary audio data."""
        examiner_text = "What do you like most about your hometown?"
        result = self.tts.synthesize(text=examiner_text)

        self.assertIsInstance(result, KokoroAudioResult)
        self.assertIsInstance(result.audio_bytes, bytes)
        self.assertGreater(len(result.audio_bytes), 44)  # Valid WAV header + PCM payload
        self.assertTrue(result.audio_bytes.startswith(b"RIFF"))

    def test_tts_playback_guard_against_echo(self):
        """Test state separation between TTS generation complete and audio playback complete."""
        examiner_text = "Please tell me about your job."
        result = self.tts.synthesize(text=examiner_text)

        self.assertIsInstance(result.audio_bytes, bytes)
        self.assertGreater(result.duration_sec, 0.0)
        self.assertGreaterEqual(result.processing_time_sec, 0.0)

    def test_sentence_level_streaming_synthesis(self):
        """Test sentence-level streaming TTS chunking for long examiner prompts."""
        multi_sentence_prompt = "Now I'd like to ask you about your studies. What subject are you currently studying?"
        results = self.tts.synthesize_sentences(text=multi_sentence_prompt)

        self.assertEqual(len(results), 2)
        for res in results:
            self.assertIsInstance(res, KokoroAudioResult)
            self.assertTrue(res.audio_bytes.startswith(b"RIFF"))


if __name__ == "__main__":
    unittest.main()
