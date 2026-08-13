import os
import sys
import struct
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from audio.vad import (
    BaseVAD,
    EnergyVAD,
    SileroVAD,
    VADState,
    VADSegmenter
)


def create_pcm_frame(amplitude: int, frame_duration_ms: int = 30, sample_rate: int = 16000) -> bytes:
    """
    Helper function generating constant amplitude 16kHz 16-bit PCM mono frame.
    30ms at 16kHz = 480 samples = 960 bytes.
    """
    sample_count = int((sample_rate * frame_duration_ms) / 1000)
    samples = [amplitude] * sample_count
    return struct.pack(f"<{sample_count}h", *samples)


def test_energy_vad_probability_calculation():
    print("--- Test 1: EnergyVAD Probability Calculation ---")
    vad = EnergyVAD(energy_threshold=300.0, max_energy=3000.0)

    # 1. Silence frame (amplitude = 10)
    silence_frame = create_pcm_frame(amplitude=10)
    prob_silence = vad.get_speech_probability(silence_frame)
    assert prob_silence < 0.2
    assert not vad.is_speech(silence_frame, threshold=0.5)
    print(f"✓ Silence frame probability: {prob_silence:.3f} (< 0.2, Speech = False)")

    # 2. Speech frame (amplitude = 1500)
    speech_frame = create_pcm_frame(amplitude=1500)
    prob_speech = vad.get_speech_probability(speech_frame)
    assert prob_speech > 0.6
    assert vad.is_speech(speech_frame, threshold=0.5)
    print(f"✓ Speech frame probability: {prob_speech:.3f} (> 0.6, Speech = True)")


def test_silero_vad_fallback():
    print("\n--- Test 2: SileroVAD Fallback & Interface ---")
    silero = SileroVAD(threshold=0.5)
    
    silence_frame = create_pcm_frame(amplitude=5)
    speech_frame = create_pcm_frame(amplitude=2000)

    prob_silence = silero.get_speech_probability(silence_frame)
    prob_speech = silero.get_speech_probability(speech_frame)

    assert prob_silence < 0.3
    assert prob_speech > 0.6
    print(f"✓ SileroVAD executed successfully (Silence prob: {prob_silence:.3f}, Speech prob: {prob_speech:.3f}).")


def test_vad_segmenter_pre_roll_and_post_roll():
    print("\n--- Test 3: VADSegmenter Pre-Roll & Post-Roll Retention ---")
    segmenter = VADSegmenter(
        vad_engine=EnergyVAD(energy_threshold=300.0),
        frame_duration_ms=30,
        pre_roll_ms=300,  # 10 frames
        post_roll_ms=300, # 10 frames
        min_speech_ms=90, # 3 frames
        silence_threshold_ms=150 # 5 frames
    )

    silence_frame = create_pcm_frame(amplitude=10)   # Silence frame
    speech_frame = create_pcm_frame(amplitude=1500)  # Speech frame

    # Feed 5 frames of silence to fill pre-roll
    for _ in range(5):
        res = segmenter.process_frame(silence_frame)
        assert res["state"] == "LISTENING"
    print("✓ Pre-roll silence frames accumulated in LISTENING state.")

    # Feed 4 frames of speech
    for _ in range(4):
        res = segmenter.process_frame(speech_frame)

    assert res["state"] in ("SPEECH_DETECTED", "IN_SPEECH")
    assert res["is_speech"] is True
    print(f"✓ State transitioned to '{res['state']}' on speech detection.")

    # Feed silence frames until endpoint reached (5 frames = 150ms)
    final_res = None
    for _ in range(6):
        res = segmenter.process_frame(silence_frame)
        if res["is_finalized"]:
            final_res = res
            break

    assert final_res is not None
    assert final_res["is_finalized"] is True
    assert final_res["state"] == "SPEECH_COMPLETE"
    assert final_res["audio"] is not None
    assert len(final_res["audio"]) > 0
    print(f"✓ Speech turn finalized with complete audio segment ({final_res['duration_sec']}s).")


def test_ielts_mode_silence_thresholds():
    print("\n--- Test 4: IELTS Part Mode Silence Thresholds ---")
    segmenter = VADSegmenter()

    segmenter.set_ielts_mode("part1")
    assert segmenter.silence_threshold_ms == 1200
    print("✓ Part 1 silence threshold = 1200 ms.")

    segmenter.set_ielts_mode("part2")
    assert segmenter.silence_threshold_ms == 2000
    print("✓ Part 2 silence threshold = 2000 ms.")

    segmenter.set_ielts_mode("part3")
    assert segmenter.silence_threshold_ms == 1500
    print("✓ Part 3 silence threshold = 1500 ms.")


def main():
    print("===============================================================")
    print("   Running Lesson 44 Unit & Integration Test Suite            ")
    print("===============================================================")
    test_energy_vad_probability_calculation()
    test_silero_vad_fallback()
    test_vad_segmenter_pre_roll_and_post_roll()
    test_ielts_mode_silence_thresholds()
    print("\n✓ ALL LESSON 44 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
