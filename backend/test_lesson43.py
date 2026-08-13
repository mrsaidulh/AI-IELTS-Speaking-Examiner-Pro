import os
import sys
import struct
import wave
import io
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio.buffer import AudioBuffer
from websocket.protocol import (
    WebSocketState,
    WebSocketEventType,
    format_ws_event
)
from websocket.events import handle_websocket_message, ws_manager


def test_audio_buffer_pcm_accumulation():
    print("--- Test 1: AudioBuffer PCM Accumulation & Conversion ---")
    
    buf = AudioBuffer(sample_rate=16000, channels=1, sample_width=2)
    assert buf.get_duration_seconds() == 0.0
    assert buf.get_sample_count() == 0
    assert buf.get_chunk_count() == 0

    # Test Float32 -> PCM16 conversion
    float_samples = [-1.0, -0.5, 0.0, 0.5, 1.0]
    pcm_bytes = AudioBuffer.float32_to_pcm16(float_samples)
    assert len(pcm_bytes) == 10  # 5 samples * 2 bytes = 10 bytes

    # Unpack 16-bit signed shorts
    unpacked = struct.unpack("<5h", pcm_bytes)
    assert unpacked[0] == -32768
    assert unpacked[2] == 0
    assert unpacked[4] == 32767
    print("✓ Float32 -> PCM16 conversion verified (-1.0 -> -32768, 0.0 -> 0, 1.0 -> 32767).")

    # Append float array to buffer
    buf.append_float_array(float_samples)
    assert buf.get_sample_count() == 5
    assert buf.get_chunk_count() == 1
    print("✓ Append float array verified.")


def test_audio_buffer_duration_and_wav_export():
    print("\n--- Test 2: AudioBuffer Duration & WAV Header Export ---")

    buf = AudioBuffer(sample_rate=16000, channels=1, sample_width=2)
    
    # 1 second of 16kHz Mono 16-bit audio = 16,000 samples = 32,000 bytes
    dummy_pcm = b"\x00\x00" * 16000
    buf.append_chunk(dummy_pcm)

    assert len(buf.get_pcm_bytes()) == 32000
    assert buf.get_sample_count() == 16000
    assert buf.get_duration_seconds() == 1.0
    print("✓ 1.0 second audio buffer duration calculation verified.")

    # Export WAV bytes and verify RIFF/WAV header
    wav_data = buf.export_wav_bytes()
    assert wav_data.startswith(b"RIFF")
    
    with wave.open(io.BytesIO(wav_data), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 16000
        assert wav_file.getnframes() == 16000
    print("✓ WAV header export verified (16kHz, Mono, 16-bit, 16000 frames).")

    buf.clear()
    assert buf.get_duration_seconds() == 0.0
    assert len(buf.get_pcm_bytes()) == 0
    print("✓ AudioBuffer reset and cleared successfully.")


class MockWebSocket:
    def __init__(self):
        self.sent_events = []

    async def accept(self):
        pass

    async def send_text(self, text: str):
        pass

    async def send_bytes(self, data: bytes):
        pass


async def test_websocket_audio_event_flow():
    print("\n--- Test 3: WebSocket Audio Event Flow (audio_start -> audio_chunk -> audio_end) ---")

    mock_ws = MockWebSocket()
    session_id = "test_audio_session"
    await ws_manager.connect(session_id, mock_ws)

    # 1. audio_start
    start_msg = {"type": "audio_start", "data": {"sample_rate": 16000, "channels": 1}}
    res_start = await handle_websocket_message(session_id, mock_ws, start_msg)
    assert res_start["data"]["state"] == "LISTENING"
    print("✓ 'audio_start' initialized LISTENING state and cleared buffer.")

    # 2. Binary audio chunk appended to WebSocketManager buffer
    chunk_1s = b"\x10\x00" * 16000  # 1 second chunk
    ws_manager.append_audio_chunk(session_id, chunk_1s)
    
    audio_buf = ws_manager.audio_buffers[session_id]
    assert audio_buf.get_duration_seconds() == 1.0
    print("✓ Binary audio chunk appended directly to session AudioBuffer.")

    # 3. audio_chunk control event
    chunk_msg = {"type": "audio_chunk", "data": {"samples": [0.1] * 1600}}  # 0.1s chunk
    res_chunk = await handle_websocket_message(session_id, mock_ws, chunk_msg)
    assert res_chunk["data"]["state"] == "LISTENING"
    assert res_chunk["data"]["buffered_duration_sec"] >= 1.0
    print("✓ 'audio_chunk' control message parsed and appended samples.")

    # 4. audio_end
    end_msg = {"type": "audio_end", "data": {}}
    res_end = await handle_websocket_message(session_id, mock_ws, end_msg)
    assert res_end["data"]["state"] == "PROCESSING"
    assert res_end["data"]["audio_duration_sec"] > 1.0
    print("✓ 'audio_end' finalized buffering and reported duration metrics.")

    ws_manager.disconnect(session_id)


async def main():
    print("===============================================================")
    print("   Running Lesson 43 Unit & Integration Test Suite            ")
    print("===============================================================")
    test_audio_buffer_pcm_accumulation()
    test_audio_buffer_duration_and_wav_export()
    await test_websocket_audio_event_flow()
    print("\n✓ ALL LESSON 43 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(main())
