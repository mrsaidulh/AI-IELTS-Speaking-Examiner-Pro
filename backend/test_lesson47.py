import sys
import os
import asyncio
import wave
import io
import struct

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from speech.whisper_service import WhisperService
from speech.schema import Transcript, TranscriptSegment
from websocket.protocol import WebSocketEventType, WebSocketState
from websocket.events import ws_manager, handle_websocket_message
from examiner.controller import ExaminerController
from qwen_service import QwenService


class MockWebSocket:
    """
    Mock WebSocket for capturing events emitted by WebSocketManager.
    """
    def __init__(self):
        self.sent_events = []
        self.sent_bytes = []
        self.is_closed = False

    async def accept(self):
        pass

    async def send_text(self, text: str):
        import json
        self.sent_events.append(json.loads(text))

    async def send_bytes(self, data: bytes):
        self.sent_bytes.append(data)


def generate_pcm16_wav_bytes(duration_sec: float = 1.0, sample_rate: int = 16000) -> bytes:
    """
    Helper to create WAV bytes containing synthetic PCM16 audio.
    """
    num_samples = int(sample_rate * duration_sec)
    pcm_samples = [int(10000 * (i % 20 - 10) / 10) for i in range(num_samples)]
    raw_pcm = struct.pack(f"<{num_samples}h", *pcm_samples)
    
    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(raw_pcm)
    return wav_io.getvalue()


async def run_lesson47_tests():
    print("===============================================================")
    print("   Running Lesson 47 Unit & Integration Test Suite            ")
    print("===============================================================")

    # --- Test 1: Partial vs Final Transcript Schema & Whisper Methods ---
    print("\n--- Test 1: Partial vs Final Transcript Schema & Whisper Methods ---")
    whisper = WhisperService()
    wav_1s = generate_pcm16_wav_bytes(1.0)
    
    partial_tx = whisper.transcribe_partial(wav_1s)
    assert isinstance(partial_tx, Transcript), "Partial transcription must return a Transcript object"
    assert partial_tx.is_partial is True, "is_partial must be True for partial transcription"
    assert partial_tx.text != "", "Partial text must not be empty"
    
    final_tx = whisper.transcribe_final(wav_1s)
    assert isinstance(final_tx, Transcript), "Final transcription must return a Transcript object"
    assert final_tx.is_partial is False, "is_partial must be False for final transcription"
    assert "Mymensingh" in final_tx.text or "peaceful" in final_tx.text or len(final_tx.text) > 0
    
    dump_partial = partial_tx.model_dump()
    assert dump_partial.get("is_partial") is True
    
    dump_final = final_tx.model_dump()
    assert dump_final.get("is_partial") is False

    print(f"✓ Partial Transcript verified: '{partial_tx.text}' (is_partial={partial_tx.is_partial})")
    print(f"✓ Final Transcript verified: '{final_tx.text}' (is_partial={final_tx.is_partial})")

    # --- Test 2: Audio Chunk Streaming & Partial Transcription (No Qwen Call) ---
    print("\n--- Test 2: Audio Chunk Streaming & Partial Transcription (No Qwen Call) ---")
    session_id = "test_lesson47_session"
    mock_ws = MockWebSocket()
    
    # Connect session
    await ws_manager.connect(session_id, mock_ws)
    mock_ws.sent_events.clear()

    # Send audio start
    msg_start = {"type": WebSocketEventType.AUDIO_START.value, "data": {}}
    _ = await handle_websocket_message(session_id, mock_ws, msg_start)

    # Send 1.0s audio chunk
    num_samples = 16000
    float_samples = [0.1 * (i % 10 - 5) for i in range(num_samples)]
    msg_chunk = {
        "type": WebSocketEventType.AUDIO_CHUNK.value,
        "data": {"samples": float_samples}
    }
    
    res_chunk = await handle_websocket_message(session_id, mock_ws, msg_chunk)
    assert res_chunk["type"] == "state"
    assert res_chunk["data"]["state"] == WebSocketState.LISTENING.value

    # Check that transcript.partial event was sent to client UI
    partial_events = [e for e in mock_ws.sent_events if e.get("type") == WebSocketEventType.TRANSCRIPT_PARTIAL.value]
    assert len(partial_events) > 0, "transcript.partial event must be emitted during audio chunk buffering"
    p_evt = partial_events[0]
    assert p_evt["data"]["is_partial"] is True
    assert p_evt["data"]["text"] != ""
    print(f"✓ Received transcript.partial event over WebSocket: '{p_evt['data']['text']}'")

    # Verify that NO examiner response (Qwen call) occurred during partial streaming
    examiner_events = [e for e in mock_ws.sent_events if e.get("type") == WebSocketEventType.EXAMINER_RESPONSE.value]
    assert len(examiner_events) == 0, "Partial transcription MUST NOT trigger Qwen/Examiner response!"
    print("✓ Confirmed: transcript.partial strictly updated UI and NEVER triggered Qwen/Examiner!")

    # --- Test 3: Audio End Final Transcription & Qwen Trigger ---
    print("\n--- Test 3: Audio End Final Transcription & Qwen Trigger ---")
    msg_end = {"type": WebSocketEventType.AUDIO_END.value, "data": {}}
    res_end = await handle_websocket_message(session_id, mock_ws, msg_end)

    # Check that transcript.final event was sent to client UI
    final_events = [e for e in mock_ws.sent_events if e.get("type") == WebSocketEventType.TRANSCRIPT_FINAL.value]
    assert len(final_events) > 0, "transcript.final event must be emitted on audio_end"
    f_evt = final_events[0]
    assert f_evt["data"]["is_partial"] is False
    assert f_evt["data"]["text"] != ""
    print(f"✓ Received transcript.final event over WebSocket: '{f_evt['data']['text']}'")

    # Verify that examiner response WAS triggered on final transcript
    examiner_events = [e for e in mock_ws.sent_events if e.get("type") == WebSocketEventType.EXAMINER_RESPONSE.value]
    assert len(examiner_events) > 0, "Final transcript MUST trigger Examiner response!"
    ex_evt = examiner_events[0]
    assert ex_evt["data"]["text"] != ""
    print(f"✓ Confirmed: transcript.final successfully triggered Examiner response: '{ex_evt['data']['text'][:50]}...'")

    # Cleanup session
    ws_manager.disconnect(session_id)

    # --- Test 4: Audio Buffer Window Thresholding ---
    print("\n--- Test 4: Audio Buffer Window Thresholding ---")
    session_id_2 = "test_lesson47_threshold"
    mock_ws_2 = MockWebSocket()
    await ws_manager.connect(session_id_2, mock_ws_2)
    mock_ws_2.sent_events.clear()

    # Send tiny 0.1s chunk (< 0.3s threshold)
    tiny_samples = [0.05] * 1600 # 0.1s at 16kHz
    msg_tiny = {
        "type": WebSocketEventType.AUDIO_CHUNK.value,
        "data": {"samples": tiny_samples}
    }
    await handle_websocket_message(session_id_2, mock_ws_2, msg_tiny)
    
    partial_events_tiny = [e for e in mock_ws_2.sent_events if e.get("type") == WebSocketEventType.TRANSCRIPT_PARTIAL.value]
    assert len(partial_events_tiny) == 0, "Chunks below 0.3s threshold must not generate partial transcript overhead"
    print("✓ Chunks under 0.3s threshold safely accumulated without unnecessary partial ASR overhead.")

    ws_manager.disconnect(session_id_2)

    print("\n✓ ALL LESSON 47 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(run_lesson47_tests())
