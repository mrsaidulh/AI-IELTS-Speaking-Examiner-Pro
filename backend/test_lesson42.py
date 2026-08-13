import os
import sys
import json
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from websocket.protocol import (
    WebSocketState,
    WebSocketEventType,
    format_ws_event,
    format_state_event,
    format_error_event
)
from websocket.events import handle_websocket_message, ws_manager
from examiner.controller import ExaminerController
from examiner.actions import ExaminerAction


class MockWebSocket:
    """
    Mock WebSocket for testing event sending/receiving without a network server.
    """
    def __init__(self):
        self.sent_events = []
        self.closed = False

    async def accept(self):
        pass

    async def send_text(self, text: str):
        self.sent_events.append(json.loads(text))

    async def send_bytes(self, data: bytes):
        self.sent_events.append({"binary_bytes_length": len(data)})


async def test_protocol_formatting():
    print("--- Test 1: WebSocket Protocol Event Formatting ---")
    
    event = format_ws_event(WebSocketEventType.SPEECH_START.value)
    assert event["type"] == "speech_start"
    assert event["data"] == {}
    print("✓ Basic event structure matches {'type': ..., 'data': {}}")

    state_evt = format_state_event(WebSocketState.LISTENING, {"details": "Candidate speaking"})
    assert state_evt["type"] == "state"
    assert state_evt["data"]["state"] == "LISTENING"
    assert state_evt["data"]["details"] == "Candidate speaking"
    print("✓ State transition event correctly formatted.")

    err_evt = format_error_event("Invalid state transition", code="ERR_STATE")
    assert err_evt["type"] == "error"
    assert err_evt["data"]["message"] == "Invalid state transition"
    print("✓ Error event correctly formatted.")


async def test_session_isolation_and_manager():
    print("\n--- Test 2: Session Isolation & Connection Manager ---")

    mock_ws1 = MockWebSocket()
    mock_ws2 = MockWebSocket()

    session_a = "session_8f92c1"
    session_b = "session_9a73b2"

    ctrl_a = await ws_manager.connect(session_a, mock_ws1)
    ctrl_b = await ws_manager.connect(session_b, mock_ws2)

    assert ctrl_a.session.session_id == session_a
    assert ctrl_b.session.session_id == session_b
    assert ctrl_a is not ctrl_b
    print("✓ Session A and Session B maintain isolated ExaminerController instances.")

    # Disconnect Session A
    ws_manager.disconnect(session_a)
    assert session_a not in ws_manager.active_connections
    assert session_b in ws_manager.active_connections
    print("✓ Disconnection of Session A did not impact Session B.")


async def test_event_routing_and_state_machine():
    print("\n--- Test 3: WebSocket Event Routing & State Machine ---")

    mock_ws = MockWebSocket()
    session_id = "test_ws_session"
    await ws_manager.connect(session_id, mock_ws)

    # 1. Ping -> Pong
    ping_msg = {"type": "ping", "data": {"timestamp": 123456789}}
    res_pong = await handle_websocket_message(session_id, mock_ws, ping_msg)
    assert res_pong["type"] == "pong"
    assert res_pong["data"]["timestamp"] == 123456789
    print("✓ 'ping' control event routed to 'pong' response.")

    # 2. session_start -> READY & EXAMINER_SPEAKING
    start_msg = {"type": "session_start", "data": {}}
    res_start = await handle_websocket_message(session_id, mock_ws, start_msg)
    assert res_start["data"]["state"] == "LISTENING"
    print("✓ 'session_start' routed and initialized session state to LISTENING.")

    # 3. speech_start -> LISTENING
    sp_start_msg = {"type": "speech_start", "data": {}}
    res_sp_start = await handle_websocket_message(session_id, mock_ws, sp_start_msg)
    assert res_sp_start["data"]["state"] == "LISTENING"
    print("✓ 'speech_start' routed -> Candidate state updated to LISTENING.")

    # 4. speech_end with transcript -> PROCESSING -> EXAMINER_SPEAKING
    sp_end_msg = {
        "type": "speech_end",
        "data": {
            "transcript": "I live in Dhaka, which is a busy and vibrant capital city."
        }
    }
    res_sp_end = await handle_websocket_message(session_id, mock_ws, sp_end_msg)
    assert res_sp_end["data"]["state"] == "LISTENING"

    # Check broadcast events sent via ws_manager
    event_types = [e["type"] for e in mock_ws.sent_events]
    assert "state" in event_types
    assert "transcript" in event_types
    assert "examiner_response" in event_types
    print(f"✓ 'speech_end' routed -> Generated transcript & examiner_response. Events emitted: {set(event_types)}")

    ws_manager.disconnect(session_id)


async def main():
    print("===============================================================")
    print("   Running Lesson 42 Unit & Integration Test Suite            ")
    print("===============================================================")
    await test_protocol_formatting()
    await test_session_isolation_and_manager()
    await test_event_routing_and_state_machine()
    print("\n✓ ALL LESSON 42 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(main())
