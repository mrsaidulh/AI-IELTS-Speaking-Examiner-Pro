import unittest
import asyncio
from websocket.protocol import (
    WebSocketState,
    WebSocketEventType,
    format_ws_event,
    format_state_event,
    format_error_event,
)
from websocket.events import (
    WebSocketManager,
    handle_websocket_message,
    ws_manager,
)


class DummyWebSocket:
    def __init__(self):
        self.accepted = False
        self.sent_events = []
        self.sent_bytes = []

    async def accept(self):
        self.accepted = True

    async def send_text(self, text):
        import json
        self.sent_events.append(json.loads(text))

    async def send_bytes(self, data):
        self.sent_bytes.append(data)


class TestLesson58(unittest.TestCase):
    def setUp(self):
        self.session_id = "test_lesson58_session"
        self.ws = DummyWebSocket()

    def tearDown(self):
        ws_manager.disconnect(self.session_id)
        if self.session_id in ws_manager.controllers:
            del ws_manager.controllers[self.session_id]

    def test_websocket_manager_connect_and_reconnection_recovery(self):
        """Test connection registration, disconnect cleanup, and session state preservation for reconnect."""
        asyncio.run(ws_manager.connect(self.session_id, self.ws))
        self.assertTrue(self.ws.accepted)
        self.assertIn(self.session_id, ws_manager.active_connections)
        self.assertIn(self.session_id, ws_manager.controllers)

        # Simulating socket disconnect - connection removed but controller session state preserved for reconnect
        ws_manager.disconnect(self.session_id)
        self.assertNotIn(self.session_id, ws_manager.active_connections)
        self.assertIn(self.session_id, ws_manager.controllers)  # Controller state preserved

        # Reconnect restores active connection and same controller session
        ws2 = DummyWebSocket()
        asyncio.run(ws_manager.connect(self.session_id, ws2))
        self.assertIn(self.session_id, ws_manager.active_connections)

    def test_ping_pong_heartbeat(self):
        """Test heartbeat ping-pong message handling for connection liveness."""
        msg = {"type": "ping", "data": {"timestamp": 123456789}}
        res = asyncio.run(handle_websocket_message(self.session_id, self.ws, msg))

        self.assertEqual(res["type"], "pong")
        self.assertEqual(res["data"]["timestamp"], 123456789)

    def test_unauthorized_state_transition_blocked(self):
        """Test server authority blocking client attempts to manually set exam state/part."""
        unauthorized_msg = {"type": "set_part", "data": {"part": "part3"}}
        res = asyncio.run(handle_websocket_message(self.session_id, self.ws, unauthorized_msg))

        self.assertEqual(res["type"], "error")
        self.assertEqual(res["data"]["code"], "UNAUTHORIZED_STATE_TRANSITION")

    def test_examiner_speaking_echo_suppression(self):
        """Test candidate mic input suppression when examiner audio is actively playing."""
        asyncio.run(ws_manager.connect(self.session_id, self.ws))
        ws_manager.set_examiner_speaking(self.session_id, True)

        chunk_msg = {
            "type": "audio_chunk",
            "data": {"samples": [0.0] * 320}
        }
        res = asyncio.run(handle_websocket_message(self.session_id, self.ws, chunk_msg))

        self.assertEqual(res["data"]["state"], WebSocketState.EXAMINER_SPEAKING.value)
        self.assertTrue(res["data"].get("echo_suppressed"))


if __name__ == "__main__":
    unittest.main()
