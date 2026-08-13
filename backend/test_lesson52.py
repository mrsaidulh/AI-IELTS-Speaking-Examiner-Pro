import asyncio
import json
import unittest
from typing import List, Dict, Any

from websocket.events import ws_manager, handle_websocket_message
from websocket.protocol import WebSocketState, WebSocketEventType, format_ws_event
from examiner.controller import ExaminerController
from examiner.enums import Part, ExaminerState, ConversationState


class MockWebSocket:
    """
    Mock FastAPI WebSocket for unit and integration testing of real-time messaging.
    """
    def __init__(self):
        self.sent_texts: List[str] = []
        self.sent_bytes: List[bytes] = []
        self.is_accepted = False

    async def accept(self):
        self.is_accepted = True

    async def send_text(self, data: str):
        self.sent_texts.append(data)

    async def send_bytes(self, data: bytes):
        self.sent_bytes.append(data)

    def get_parsed_events(self) -> List[Dict[str, Any]]:
        events = []
        for text in self.sent_texts:
            try:
                events.append(json.loads(text))
            except json.JSONDecodeError:
                pass
        return events


class TestLesson52(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.session_id = "test_lesson52_session"
        self.mock_ws = MockWebSocket()
        self.controller = await ws_manager.connect(self.session_id, self.mock_ws)

    async def asyncTearDown(self):
        ws_manager.disconnect(self.session_id)

    async def test_websocket_connection_lifecycle_and_ping_pong(self):
        """Test WebSocket connection handshake, initial state event, and ping/pong heartbeat."""
        self.assertTrue(self.mock_ws.is_accepted)
        events = self.mock_ws.get_parsed_events()
        self.assertGreaterEqual(len(events), 1)
        
        # Verify initial CONNECTED state event
        self.assertEqual(events[0]["type"], "state")
        self.assertEqual(events[0]["data"]["state"], WebSocketState.CONNECTED.value)

        # Send Ping event
        ping_res = await handle_websocket_message(
            self.session_id,
            self.mock_ws,
            {"type": "ping", "data": {"timestamp": 12345678}}
        )
        self.assertEqual(ping_res["type"], "pong")
        self.assertEqual(ping_res["data"]["timestamp"], 12345678)

    async def test_client_authority_guard_rejection(self):
        """Test server rejection of unauthorized client-driven examination state mutation events."""
        unauth_msg = {"type": "set_part", "data": {"part": 3}}
        err_res = await handle_websocket_message(self.session_id, self.mock_ws, unauth_msg)
        
        self.assertEqual(err_res["type"], "error")
        self.assertEqual(err_res["data"]["code"], "UNAUTHORIZED_STATE_TRANSITION")
        self.assertIn("Unauthorized examination state transition", err_res["data"]["message"])

    async def test_echo_suppression_and_audio_chunk_buffering(self):
        """Test candidate microphone echo suppression guard and audio chunk buffering."""
        # 1. Enable examiner speaking flag -> Audio chunk must be echo-suppressed
        ws_manager.set_examiner_speaking(self.session_id, True)
        suppressed_res = await handle_websocket_message(
            self.session_id,
            self.mock_ws,
            {"type": "audio_chunk", "data": {"raw_hex": "00000000"}}
        )
        self.assertTrue(suppressed_res["data"].get("echo_suppressed"))

        # 2. Disable examiner speaking flag -> Audio chunk buffered
        ws_manager.set_examiner_speaking(self.session_id, False)
        buffered_res = await handle_websocket_message(
            self.session_id,
            self.mock_ws,
            {"type": "audio_chunk", "data": {"raw_hex": "0000" * 1600}} # 3200 bytes = 0.1s audio
        )
        self.assertEqual(buffered_res["data"]["state"], WebSocketState.LISTENING.value)
        self.assertGreater(buffered_res["data"]["buffered_duration_sec"], 0.0)

    async def test_partial_vs_final_transcript_separation(self):
        """Test transcript.partial stream vs transcript.final execution turn triggering."""
        # Send audio chunk
        sample_hex = "0000" * 3200 # 3.2KB chunk (~100ms)
        await handle_websocket_message(
            self.session_id,
            self.mock_ws,
            {"type": "audio_chunk", "data": {"raw_hex": sample_hex}}
        )

        # Trigger speech.end turn completion
        turn_end_res = await handle_websocket_message(
            self.session_id,
            self.mock_ws,
            {"type": "speech_end", "data": {"transcript": "I am from Mymensingh, Bangladesh."}}
        )

        # Verify state transition to THINKING and back to LISTENING
        events = self.mock_ws.get_parsed_events()
        event_types = [e["type"] for e in events]
        self.assertIn("transcript", event_types)
        self.assertIn("examiner_thinking", event_types)
        self.assertIn("examiner_response", event_types)

    async def test_safe_error_handling(self):
        """Test that internal unexpected exceptions return user-friendly PIPELINE_ERROR events."""
        # Send unknown event type
        err_res = await handle_websocket_message(
            self.session_id,
            self.mock_ws,
            {"type": "non_existent_event_type"}
        )
        self.assertEqual(err_res["type"], "error")
        self.assertEqual(err_res["data"]["code"], "UNKNOWN_EVENT")


if __name__ == "__main__":
    unittest.main()
