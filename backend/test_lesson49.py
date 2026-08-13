import os
import sys
import asyncio
import json
import base64
import time

# Ensure backend directory is in python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from speech.kokoro_service import KokoroService, KokoroAudioResult
from websocket.events import ws_manager, handle_websocket_message
from websocket.protocol import (
    WebSocketState,
    WebSocketEventType,
    format_ws_event
)


class MockWebSocket:
    """
    In-memory Mock WebSocket for asynchronous event pipeline validation.
    """
    def __init__(self):
        self.sent_events = []
        self.closed = False

    async def accept(self):
        pass

    async def send_text(self, data: str):
        self.sent_events.append(json.loads(data))

    async def send_bytes(self, data: bytes):
        self.sent_events.append({"type": "raw_bytes", "size": len(data)})


async def run_lesson49_tests():
    print("===============================================================")
    print("   Running Lesson 49 Kokoro TTS Integration Test Suite        ")
    print("===============================================================\n")

    # --- Test 1: Kokoro Service Direct Synthesis & Audio Metadata ---
    print("--- Test 1: Kokoro Service Direct Synthesis & Audio Payload ---")
    kokoro = KokoroService(enable_cache=True)
    text = "Could you tell me about your hometown?"
    
    result = kokoro.synthesize(text)
    assert isinstance(result, KokoroAudioResult)
    assert len(result.audio_bytes) > 0
    assert len(result.audio_base64) > 0
    assert result.format == "wav"
    assert result.voice == "af_heart"
    assert result.duration_sec > 0.0
    assert result.cached is False
    print(f"✓ Synthesized text: '{result.text}' | Duration: {result.duration_sec}s | Bytes: {len(result.audio_bytes)}")

    # Test synthesize_file
    output_file = "/tmp/test_examiner_tts.wav"
    out_path = kokoro.synthesize_file("Thank you.", output_file)
    assert os.path.exists(out_path)
    print(f"✓ Saved TTS audio file successfully to: {out_path}")


    # --- Test 2: Phrase Caching & Hit Verification ---
    print("\n--- Test 2: Phrase Caching & Hit Verification ---")
    kokoro.clear_cache()
    cached_phrase = "Let's move on to Part 2."

    # First call -> cache miss
    res1 = kokoro.synthesize(cached_phrase)
    assert res1.cached is False

    # Second call -> cache hit
    res2 = kokoro.synthesize(cached_phrase)
    assert res2.cached is True
    assert res1.audio_bytes == res2.audio_bytes
    
    stats = kokoro.get_cache_stats()
    assert stats["hits"] == 1
    assert stats["cached_phrases"] == 1
    print(f"✓ Cache hit verified for phrase: '{cached_phrase}' (Cache stats: {stats})")


    # --- Test 3: Sentence-Level Text Segmentation ---
    print("\n--- Test 3: Sentence-Level Text Segmentation ---")
    multisentence = "That's an interesting topic. Could you explain why you feel that way? Let's discuss it further."
    sentences = kokoro.split_sentences(multisentence)
    assert len(sentences) == 3
    assert sentences[0] == "That's an interesting topic."
    assert sentences[1] == "Could you explain why you feel that way?"
    assert sentences[2] == "Let's discuss it further."
    print(f"✓ Sentence splitting verified across {len(sentences)} sentences: {sentences}")

    batch_results = kokoro.synthesize_sentences(multisentence)
    assert len(batch_results) == 3
    for b in batch_results:
        assert len(b.audio_bytes) > 0
    print("✓ Sentence batch TTS synthesis verified successfully.")


    # --- Test 4: Echo Suppression & Candidate Microphone Guard ---
    print("\n--- Test 4: Echo Suppression & Candidate Microphone Guard ---")
    session_id = "test_lesson49_echo_session"
    mock_ws = MockWebSocket()
    await ws_manager.connect(session_id, mock_ws)

    # Set EXAMINER_SPEAKING state
    ws_manager.set_examiner_speaking(session_id, True)
    assert ws_manager.is_examiner_speaking(session_id) is True

    # Attempt to send candidate audio chunk during examiner playback
    chunk_msg = format_ws_event(WebSocketEventType.AUDIO_CHUNK.value, {
        "raw_hex": "0000" * 160
    })
    response = await handle_websocket_message(session_id, mock_ws, chunk_msg)
    
    assert response["data"]["state"] == WebSocketState.EXAMINER_SPEAKING.value
    assert response["data"]["echo_suppressed"] is True
    print("✓ Mic echo suppression verified: Candidate audio safely ignored while examiner speaks.")

    ws_manager.set_examiner_speaking(session_id, False)
    ws_manager.disconnect(session_id)


    # --- Test 5: Full WebSocket Voice Loop with Kokoro TTS ---
    print("\n--- Test 5: Full WebSocket Voice Loop (Qwen + Kokoro TTS) ---")
    loop_session = "test_lesson49_full_loop"
    loop_ws = MockWebSocket()
    await ws_manager.connect(loop_session, loop_ws)

    # 1. Start Session
    start_msg = format_ws_event(WebSocketEventType.SESSION_START.value, {})
    await handle_websocket_message(loop_session, loop_ws, start_msg)

    # Check that examiner_audio event with base64 payload was emitted over WebSocket
    audio_events = [e for e in loop_ws.sent_events if e.get("type") == WebSocketEventType.EXAMINER_AUDIO.value]
    response_events = [e for e in loop_ws.sent_events if e.get("type") == WebSocketEventType.EXAMINER_RESPONSE.value]
    
    assert len(audio_events) >= 1
    assert len(response_events) >= 1
    
    first_audio = audio_events[0]["data"]
    assert "audio_base64" in first_audio
    assert len(first_audio["audio_base64"]) > 0
    assert first_audio["format"] == "wav"
    print(f"✓ Received initial Kokoro TTS audio event (Format: {first_audio['format']}, Voice: {first_audio['voice']})")

    # 2. Candidate Speech End Answer
    speech_end_msg = format_ws_event(WebSocketEventType.SPEECH_END.value, {
        "transcript": "I live in Mymensingh which is a beautiful city in Bangladesh."
    })
    loop_ws.sent_events.clear()
    await handle_websocket_message(loop_session, loop_ws, speech_end_msg)

    new_audio_events = [e for e in loop_ws.sent_events if e.get("type") == WebSocketEventType.EXAMINER_AUDIO.value]
    new_response_events = [e for e in loop_ws.sent_events if e.get("type") == WebSocketEventType.EXAMINER_RESPONSE.value]

    assert len(new_audio_events) >= 1
    assert len(new_response_events) >= 1

    turn_audio = new_audio_events[0]["data"]
    assert turn_audio["text"] == new_response_events[0]["data"]["text"]
    assert len(turn_audio["audio_base64"]) > 0
    print(f"✓ Verified full turn loop: Qwen Examiner Response -> Kokoro TTS Audio Payload generated over WebSocket.")

    ws_manager.disconnect(loop_session)

    print("\n✓ ALL LESSON 49 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(run_lesson49_tests())
