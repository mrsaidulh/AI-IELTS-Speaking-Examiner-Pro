import asyncio
import unittest
import json
import base64
import time
from typing import List, Dict, Any

from speech.pipeline import RealtimeVoiceOrchestrator
from speech.schema import SpeakingTurn
from speech.whisper_service import WhisperService
from speech.kokoro_service import KokoroService
from qwen_service import QwenService
from examiner.controller import ExaminerController
from audio.buffer import AudioBuffer
from audio.turn_detector import TurnDetector
from websocket.protocol import WebSocketState, WebSocketEventType, format_ws_event
from websocket.events import ws_manager, handle_websocket_message, emit_examiner_turn_with_tts


class DummyWebSocket:
    """Mock WebSocket client for unit testing WebSocket event streaming."""
    def __init__(self):
        self.sent_events: List[Dict[str, Any]] = []
        self.is_accepted = False

    async def accept(self):
        self.is_accepted = True

    async def send_text(self, text_data: str):
        self.sent_events.append(json.loads(text_data))

    async def send_bytes(self, byte_data: bytes):
        self.sent_events.append({"type": "binary_bytes", "size": len(byte_data)})


class TestLesson50(unittest.TestCase):
    def setUp(self):
        self.session_id = "test_lesson50_session"
        self.orchestrator = RealtimeVoiceOrchestrator(session_id=self.session_id)
        self.mock_ws = DummyWebSocket()

    def test_orchestrator_initialization(self):
        """Test that RealtimeVoiceOrchestrator properly instantiates all AI pipeline components."""
        self.assertIsNotNone(self.orchestrator.whisper)
        self.assertIsNotNone(self.orchestrator.qwen)
        self.assertIsNotNone(self.orchestrator.kokoro)
        self.assertIsNotNone(self.orchestrator.controller)
        self.assertIsNotNone(self.orchestrator.turn_detector)
        self.assertEqual(self.orchestrator.session_id, self.session_id)

    def test_execute_voice_turn(self):
        """Test end-to-end turn execution with latency tracking and SpeakingTurn object generation."""
        # Generate 1 second of 16kHz PCM audio
        dummy_pcm = b"\x00\x00" * 16000
        
        async def run_turn():
            result = await self.orchestrator.execute_voice_turn(
                candidate_audio_bytes=dummy_pcm,
                examiner_question_override="Where do you live?"
            )
            return result

        result = asyncio.run(run_turn())
        
        self.assertIn("turn_id", result)
        self.assertEqual(result["turn_number"], 1)
        self.assertIn("candidate_transcript", result)
        self.assertIn("examiner_response", result)
        self.assertIn("audio_base64", result)
        self.assertIn("latency_metrics", result)
        
        metrics = result["latency_metrics"]
        self.assertIn("asr_ms", metrics)
        self.assertIn("qwen_ms", metrics)
        self.assertIn("tts_ms", metrics)
        self.assertIn("total_ms", metrics)

        self.assertEqual(len(self.orchestrator.turns), 1)
        turn_obj: SpeakingTurn = self.orchestrator.turns[0]
        self.assertEqual(turn_obj.session_id, self.session_id)
        self.assertTrue(turn_obj.id.startswith("turn_001_"))

    def test_websocket_pipeline_session_start(self):
        """Test session.start event sequence initiating the examiner prompt and TTS voice generation."""
        async def run_session_start():
            await ws_manager.connect(self.session_id, self.mock_ws)
            msg = format_ws_event(WebSocketEventType.SESSION_START.value)
            res = await handle_websocket_message(self.session_id, self.mock_ws, msg)
            return res

        asyncio.run(run_session_start())

        event_types = [evt.get("type") for evt in self.mock_ws.sent_events]
        self.assertIn(WebSocketEventType.STATE.value, event_types)
        self.assertIn(WebSocketEventType.EXAMINER_TEXT.value, event_types)
        self.assertIn(WebSocketEventType.EXAMINER_AUDIO.value, event_types)
        self.assertIn(WebSocketEventType.EXAMINER_RESPONSE.value, event_types)
        self.assertIn(WebSocketEventType.EXAMINER_FINISHED.value, event_types)
        self.assertIn(WebSocketEventType.LISTENING_STARTED.value, event_types)

        ws_manager.disconnect(self.session_id)

    def test_websocket_full_voice_turn_sequence(self):
        """Test full conversational turn: candidate audio chunks -> transcript.partial -> speech.ended -> transcript.final -> THINKING -> EXAMINER_SPEAKING -> LISTENING."""
        async def run_voice_turn():
            await ws_manager.connect(self.session_id, self.mock_ws)
            
            # 1. Start audio stream
            await handle_websocket_message(
                self.session_id, self.mock_ws, format_ws_event(WebSocketEventType.AUDIO_START.value)
            )

            # 2. Send 0.5s PCM audio chunk
            pcm_chunk = b"\x10\x00" * 8000
            chunk_hex = pcm_chunk.hex()
            await handle_websocket_message(
                self.session_id,
                self.mock_ws,
                format_ws_event(WebSocketEventType.AUDIO_CHUNK.value, {"raw_hex": chunk_hex})
            )

            # 3. Send speech end with candidate text answer
            await handle_websocket_message(
                self.session_id,
                self.mock_ws,
                format_ws_event(WebSocketEventType.SPEECH_END.value, {"transcript": "I live in Dhaka, Bangladesh."})
            )

        asyncio.run(run_voice_turn())

        event_types = [evt.get("type") for evt in self.mock_ws.sent_events]
        self.assertIn(WebSocketEventType.TRANSCRIPT.value, event_types)
        self.assertIn(WebSocketEventType.EXAMINER_THINKING.value, event_types)
        self.assertIn(WebSocketEventType.EXAMINER_TEXT.value, event_types)
        self.assertIn(WebSocketEventType.EXAMINER_AUDIO.value, event_types)
        self.assertIn(WebSocketEventType.EXAMINER_FINISHED.value, event_types)
        self.assertIn(WebSocketEventType.LISTENING_STARTED.value, event_types)

        states = [evt.get("data", {}).get("state") for evt in self.mock_ws.sent_events if evt.get("type") == "state"]
        self.assertIn(WebSocketState.THINKING.value, states)
        self.assertIn(WebSocketState.EXAMINER_SPEAKING.value, states)
        self.assertIn(WebSocketState.LISTENING.value, states)

        ws_manager.disconnect(self.session_id)

    def test_mic_echo_suppression_guard(self):
        """Test candidate microphone input suppression when examiner AI is currently speaking."""
        async def run_echo_guard():
            await ws_manager.connect(self.session_id, self.mock_ws)
            ws_manager.set_examiner_speaking(self.session_id, True)

            pcm_chunk = b"\x00\x00" * 1000
            res = await handle_websocket_message(
                self.session_id,
                self.mock_ws,
                format_ws_event(WebSocketEventType.AUDIO_CHUNK.value, {"raw_hex": pcm_chunk.hex()})
            )
            return res

        res = asyncio.run(run_echo_guard())
        self.assertEqual(res.get("data", {}).get("state"), WebSocketState.EXAMINER_SPEAKING.value)
        self.assertTrue(res.get("data", {}).get("echo_suppressed"))

        ws_manager.disconnect(self.session_id)


if __name__ == "__main__":
    unittest.main()
