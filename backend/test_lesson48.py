#!/usr/bin/env python3
"""
Lesson 48 Unit & Integration Test Suite — Speech Endpointing & Conversation Turn Detection
Tests state transitions, IELTS Part dynamic silence thresholds, hard max duration timers,
transient noise guards, and WebSocket speech turn event emission.
"""

import sys
import asyncio
import math
import struct
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from audio.turn_detector import TurnDetector, TurnState
from audio.vad import EnergyVAD
from websocket.protocol import WebSocketEventType, WebSocketState
from websocket.events import ws_manager, handle_websocket_message


def generate_pcm_sine_wave(duration_sec: float = 0.5, freq: float = 440.0, sample_rate: int = 16000, amplitude: float = 0.5) -> bytes:
    """
    Generates 16kHz 16-bit Mono PCM sine wave audio bytes (simulating speech).
    """
    num_samples = int(sample_rate * duration_sec)
    samples = [
        int(math.sin(2 * math.pi * freq * (i / sample_rate)) * amplitude * 32767)
        for i in range(num_samples)
    ]
    return struct.pack(f"<{len(samples)}h", *samples)


def generate_pcm_silence(duration_sec: float = 0.5, sample_rate: int = 16000) -> bytes:
    """
    Generates 16kHz 16-bit Mono PCM digital silence bytes.
    """
    sample_count = int(sample_rate * duration_sec)
    return b"\x00\x00" * sample_count


class MockWebSocket:
    """
    Mock WebSocket connection to capture server-emitted JSON events.
    """
    def __init__(self):
        self.sent_events = []

    async def accept(self):
        pass

    async def send_text(self, text: str):
        import json
        self.sent_events.append(json.loads(text))

    async def send_bytes(self, data: bytes):
        pass


def test_turn_detector_state_machine_and_resumption():
    print("\n--- Test 1: TurnDetector State Machine & Resumption Flow ---")
    detector = TurnDetector(part_mode="part1", vad_engine=EnergyVAD(), min_speech_ms=300)
    
    # 1. Feed speech chunks -> enter CANDIDATE_SPEAKING
    speech_chunk = generate_pcm_sine_wave(duration_sec=0.1, amplitude=0.5)
    
    # Send 100ms
    res1 = detector.process_frame(speech_chunk, frame_duration_ms=100)
    assert res1["state"] == TurnState.LISTENING.value, "100ms speech should stay in LISTENING (under 300ms min_speech)"
    
    # Send another 200ms -> total 300ms speech
    res2 = detector.process_frame(speech_chunk, frame_duration_ms=200)
    assert res2["state"] == TurnState.CANDIDATE_SPEAKING.value
    assert res2["event_type"] == "speech.started"
    print("✓ Entered CANDIDATE_SPEAKING state upon reaching 300ms min speech.")

    # 2. Feed 200ms silence -> enter POSSIBLE_END
    silence_chunk = generate_pcm_silence(duration_sec=0.1)
    res3 = detector.process_frame(silence_chunk, frame_duration_ms=200)
    assert res3["state"] == TurnState.POSSIBLE_END.value
    assert res3["event_type"] == "speech.possible_end"
    print("✓ Entered POSSIBLE_END state during candidate mid-sentence hesitation.")

    # 3. Resume speech before silence threshold -> back to CANDIDATE_SPEAKING
    res4 = detector.process_frame(speech_chunk, frame_duration_ms=100)
    assert res4["state"] == TurnState.CANDIDATE_SPEAKING.value
    assert res4["event_type"] == "speech.resumed"
    print("✓ Successfully resumed to CANDIDATE_SPEAKING without premature turn interruption.")

    # 4. Feed silence exceeding Part 1 threshold (1200ms) -> TURN_ENDED
    for _ in range(12):  # 12 * 100ms = 1200ms
        res_silence = detector.process_frame(silence_chunk, frame_duration_ms=100)
    
    assert res_silence["state"] == TurnState.TURN_ENDED.value
    assert res_silence["event_type"] == "speech.ended"
    assert res_silence["end_reason"] == "silence_timeout"
    assert res_silence["is_finalized"] is True
    print("✓ Turn successfully ended with 'silence_timeout' after reaching Part 1 1200ms threshold.")


def test_ielts_part_dynamic_endpoint_thresholds():
    print("\n--- Test 2: IELTS Part Dynamic Silence Thresholds ---")
    
    # Part 1 (1200ms)
    td1 = TurnDetector(part_mode="part1", min_speech_ms=100)
    td1.process_frame(generate_pcm_sine_wave(0.2), frame_duration_ms=200) # Start speech
    # 1000ms silence in Part 1 -> POSSIBLE_END (not ended)
    for _ in range(10):
        r1 = td1.process_frame(generate_pcm_silence(0.1), frame_duration_ms=100)
    assert r1["state"] == TurnState.POSSIBLE_END.value
    # Additional 200ms -> 1200ms silence -> TURN_ENDED
    r1_ended = td1.process_frame(generate_pcm_silence(0.2), frame_duration_ms=200)
    assert r1_ended["state"] == TurnState.TURN_ENDED.value
    print("✓ Part 1 threshold verified (1200ms silence).")

    # Part 2 (2000ms)
    td2 = TurnDetector(part_mode="part2", min_speech_ms=100)
    td2.process_frame(generate_pcm_sine_wave(0.2), frame_duration_ms=200) # Start speech
    # 1500ms silence in Part 2 -> POSSIBLE_END (still allowed)
    for _ in range(15):
        r2 = td2.process_frame(generate_pcm_silence(0.1), frame_duration_ms=100)
    assert r2["state"] == TurnState.POSSIBLE_END.value
    # Reach 2000ms -> TURN_ENDED
    for _ in range(5):
        r2_ended = td2.process_frame(generate_pcm_silence(0.1), frame_duration_ms=100)
    assert r2_ended["state"] == TurnState.TURN_ENDED.value
    print("✓ Part 2 long-turn threshold verified (2000ms silence).")

    # Part 3 (1500ms)
    td3 = TurnDetector(part_mode="part3", min_speech_ms=100)
    td3.process_frame(generate_pcm_sine_wave(0.2), frame_duration_ms=200)
    for _ in range(15):
        r3 = td3.process_frame(generate_pcm_silence(0.1), frame_duration_ms=100)
    assert r3["state"] == TurnState.TURN_ENDED.value
    print("✓ Part 3 analytical threshold verified (1500ms silence).")


def test_hard_maximum_duration_timeout():
    print("\n--- Test 3: Hard Maximum Response Duration Timeout ---")
    td = TurnDetector(part_mode="part2", min_speech_ms=100)
    td.max_duration_sec = 2.0  # Override max duration to 2 seconds for test
    
    # Start candidate turn
    td.process_frame(generate_pcm_sine_wave(0.2), frame_duration_ms=200)
    
    # Continuously speak for 2.0s
    speech_chunk = generate_pcm_sine_wave(0.2)
    for _ in range(9): # 0.2 + 9*0.2 = 2.0s
        res = td.process_frame(speech_chunk, frame_duration_ms=200)
    
    assert res["state"] == TurnState.TURN_ENDED.value
    assert res["event_type"] == "speech.ended"
    assert res["end_reason"] == "max_duration_exceeded"
    print("✓ Forced turn termination verified upon exceeding hard maximum duration (2.0s limit).")


def test_transient_noise_guard():
    print("\n--- Test 4: Transient Noise Guard ---")
    td = TurnDetector(part_mode="part1", min_speech_ms=300)
    
    # Brief noise impulse of 100ms
    res = td.process_frame(generate_pcm_sine_wave(0.1), frame_duration_ms=100)
    assert res["state"] == TurnState.LISTENING.value
    assert res["event_type"] is None
    
    # Followed by silence
    res_silence = td.process_frame(generate_pcm_silence(0.2), frame_duration_ms=200)
    assert res_silence["state"] == TurnState.LISTENING.value
    print("✓ Transient audio noise spike (<300ms) safely ignored without false speech.started triggers.")


async def test_websocket_speech_turn_events_pipeline():
    print("\n--- Test 5: WebSocket Speech Turn Events Integration Pipeline ---")
    session_id = "test_lesson48_turn_events"
    mock_ws = MockWebSocket()
    
    await ws_manager.connect(session_id, mock_ws)
    await handle_websocket_message(session_id, mock_ws, {"type": "session_start", "data": {}})
    mock_ws.sent_events.clear()

    # 1. Stream 350ms audio chunk (speech) -> triggers speech.started
    pcm_speech = generate_pcm_sine_wave(duration_sec=0.35, amplitude=0.5)
    await handle_websocket_message(session_id, mock_ws, {
        "type": "audio_chunk",
        "data": {"raw_hex": pcm_speech.hex()}
    })
    
    started_evts = [e for e in mock_ws.sent_events if e.get("type") == "speech.started"]
    assert len(started_evts) == 1, f"Expected 1 'speech.started' event, got {len(started_evts)}"
    print("✓ Received WebSocket event 'speech.started'.")

    # 2. Stream 300ms silence -> triggers speech.possible_end
    pcm_silence = generate_pcm_silence(duration_sec=0.3)
    await handle_websocket_message(session_id, mock_ws, {
        "type": "audio_chunk",
        "data": {"raw_hex": pcm_silence.hex()}
    })

    possible_evts = [e for e in mock_ws.sent_events if e.get("type") == "speech.possible_end"]
    assert len(possible_evts) >= 1, f"Expected 'speech.possible_end' event, got {len(possible_evts)}"
    print("✓ Received WebSocket event 'speech.possible_end'.")

    # 3. Stream 200ms speech -> triggers speech.resumed
    await handle_websocket_message(session_id, mock_ws, {
        "type": "audio_chunk",
        "data": {"raw_hex": pcm_speech.hex()}
    })

    resumed_evts = [e for e in mock_ws.sent_events if e.get("type") == "speech.resumed"]
    assert len(resumed_evts) >= 1, f"Expected 'speech.resumed' event, got {len(resumed_evts)}"
    print("✓ Received WebSocket event 'speech.resumed'.")

    # 4. Stream 1400ms silence -> triggers speech.ended, transcript.final, examiner_response
    pcm_long_silence = generate_pcm_silence(duration_sec=1.4)
    await handle_websocket_message(session_id, mock_ws, {
        "type": "audio_chunk",
        "data": {"raw_hex": pcm_long_silence.hex()}
    })

    ended_evts = [e for e in mock_ws.sent_events if e.get("type") == "speech.ended"]
    assert len(ended_evts) >= 1, f"Expected 'speech.ended' event, got {len(ended_evts)}"
    print("✓ Received WebSocket event 'speech.ended'.")

    final_transcript_evts = [e for e in mock_ws.sent_events if e.get("type") == "transcript.final"]
    assert len(final_transcript_evts) >= 1, "Expected 'transcript.final' event upon speech turn completion."
    print("✓ Received WebSocket event 'transcript.final'.")

    examiner_evts = [e for e in mock_ws.sent_events if e.get("type") == "examiner_response"]
    assert len(examiner_evts) >= 1, "Expected 'examiner_response' event from Qwen/Examiner upon turn end."
    print("✓ Received WebSocket event 'examiner_response' from Examiner controller.")

    ws_manager.disconnect(session_id)


def main():
    print("===============================================================")
    print("   Running Lesson 48 Unit & Integration Test Suite            ")
    print("===============================================================")
    test_turn_detector_state_machine_and_resumption()
    test_ielts_part_dynamic_endpoint_thresholds()
    test_hard_maximum_duration_timeout()
    test_transient_noise_guard()
    asyncio.run(test_websocket_speech_turn_events_pipeline())
    print("\n✓ ALL LESSON 48 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
