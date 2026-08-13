import os
import sys
import struct

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vad import VADEngine
from speech_config import VADMode
from sessions.session import SpeakingSession

def generate_pcm_frame(amplitude: int = 0, duration_ms: int = 20, sample_rate: int = 16000) -> bytes:
    samples_count = int(sample_rate * (duration_ms / 1000.0))
    return struct.pack(f"<{samples_count}h", *[amplitude] * samples_count)

def test_vad_lifecycle():
    print("--- Running VAD Engine Lifecycle Test ---")
    session = SpeakingSession("test-session")
    session.set_part(1) # PART1 mode
    
    # 1. Send silence (IDLE state)
    silence_frame = generate_pcm_frame(amplitude=10, duration_ms=20)
    for _ in range(5):
        res = session.process_audio_chunk(silence_frame)
        assert res["state"] == "IDLE"
    print("✓ IDLE state verified with rolling pre-roll buffer.")

    # 2. Send loud speech (SPEAKING state)
    speech_frame = generate_pcm_frame(amplitude=2000, duration_ms=20)
    for _ in range(15): # 300ms speech
        res = session.process_audio_chunk(speech_frame)
    
    assert res["state"] == "SPEAKING"
    assert session.is_speaking is True
    print("✓ SPEAKING transition confirmed with energy threshold.")

    # 3. Send silence until finalized (END_SILENCE_MS = 1200ms -> 60 frames)
    finalized_res = None
    for _ in range(65):
        res = session.process_audio_chunk(silence_frame)
        if res["is_finalized"]:
            finalized_res = res
            break
            
    assert finalized_res is not None
    assert finalized_res["state"] == "FINALIZED"
    assert finalized_res["is_finalized"] is True
    assert len(finalized_res["audio"]) > 0
    print(f"✓ Speech utterance finalized successfully! Audio segment length: {len(finalized_res['audio'])} bytes.")

    # 4. Verify mode settings
    session.set_part(2) # PART2 mode (1.8s silence threshold)
    assert session.vad_engine.end_silence_ms == 1800
    print("✓ Part-specific VAD silence thresholds dynamically applied.")

if __name__ == "__main__":
    test_vad_lifecycle()
