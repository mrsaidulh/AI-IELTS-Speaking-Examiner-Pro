import os
import sys
import io
import wave
import struct
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from speech.schema import Transcript, TranscriptSegment
from speech.whisper_service import WhisperService, is_cuda_available, get_audio_duration_seconds


def create_dummy_wav_bytes(duration_sec: float = 2.0, sample_rate: int = 16000) -> bytes:
    """
    Generates valid 16kHz Mono 16-bit PCM WAV bytes for testing.
    """
    sample_count = int(sample_rate * duration_sec)
    samples = [int(1000 * (i % 2 - 0.5)) for i in range(sample_count)]
    pcm_bytes = struct.pack(f"<{sample_count}h", *samples)

    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    return wav_io.getvalue()


def test_whisper_config_env_vars():
    print("--- Test 1: Whisper Model Selection & Environment Variables ---")

    os.environ["WHISPER_MODEL"] = "base"
    os.environ["WHISPER_DEVICE"] = "cpu"
    os.environ["WHISPER_COMPUTE_TYPE"] = "int8"
    os.environ["WHISPER_LANGUAGE"] = "en"

    service = WhisperService()
    assert service.model_size == "base"
    assert service.device == "cpu"
    assert service.compute_type == "int8"
    assert service.default_language == "en"

    print("✓ Environment variable overrides verified (WHISPER_MODEL=base, WHISPER_DEVICE=cpu).")


def test_cuda_detection_and_fallback():
    print("\n--- Test 2: CUDA Device Detection & CPU Fallback ---")

    cuda_ok = is_cuda_available()
    print(f"  System CUDA available: {cuda_ok}")

    # Explicitly request CUDA
    service = WhisperService(device="cuda", compute_type="float16")

    if not cuda_ok:
        assert service.device == "cpu"
        assert service.compute_type == "int8"
        print("✓ Graceful CPU fallback verified when CUDA unavailable.")
    else:
        assert service.device == "cuda"
        assert service.compute_type == "float16"
        print("✓ CUDA GPU device successfully bound.")


def test_whisper_warmup_and_rtf_latency():
    print("\n--- Test 3: Model Warmup & Real-Time Factor (RTF) Latency ---")

    service = WhisperService(model_size="small", device="cpu", compute_type="int8")
    assert not service.is_warmed_up

    warmup_time = service.warmup()
    assert service.is_warmed_up
    assert warmup_time >= 0.0
    print(f"✓ Model warmup completed in {warmup_time}s.")

    # 2.0s audio sample
    wav_bytes = create_dummy_wav_bytes(duration_sec=2.0)
    dur = get_audio_duration_seconds(wav_bytes)
    assert dur == 2.0

    transcript = service.transcribe(wav_bytes)
    assert transcript.processing_time_sec >= 0.0
    assert transcript.rtf >= 0.0
    assert service.last_latency_sec == transcript.processing_time_sec
    assert service.last_rtf == transcript.rtf

    print(f"✓ Transcribed 2.0s audio | Latency: {transcript.processing_time_sec}s | RTF: {transcript.rtf}")


def test_whisper_benchmarking_stats():
    print("\n--- Test 4: Whisper Benchmarking Statistics Suite ---")

    service = WhisperService(model_size="small", device="cpu", compute_type="int8")
    wav_bytes = create_dummy_wav_bytes(duration_sec=1.5)

    stats = service.benchmark(wav_bytes, num_runs=5)

    assert stats["model_size"] == "small"
    assert stats["device"] == "cpu"
    assert stats["num_runs"] == 5
    assert "average_latency_sec" in stats
    assert "median_latency_sec" in stats
    assert "p95_latency_sec" in stats
    assert "average_rtf" in stats
    assert len(stats["latencies_sec"]) == 5

    print(f"✓ Benchmark completed across 5 runs:")
    print(f"  Avg Latency: {stats['average_latency_sec']}s | Median: {stats['median_latency_sec']}s | P95: {stats['p95_latency_sec']}s | Avg RTF: {stats['average_rtf']}")


def main():
    print("===============================================================")
    print("   Running Lesson 46 Unit & Integration Test Suite            ")
    print("===============================================================")
    test_whisper_config_env_vars()
    test_cuda_detection_and_fallback()
    test_whisper_warmup_and_rtf_latency()
    test_whisper_benchmarking_stats()
    print("\n✓ ALL LESSON 46 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
