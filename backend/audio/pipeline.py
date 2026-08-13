import io
import struct
import wave
import time
from typing import Dict, Any, Optional, List, Tuple
from audio.buffer import AudioBuffer
from audio.turn_detector import TurnDetector, TurnState
from audio.vad import EnergyVAD, BaseVAD


class AudioPipelineMetrics:
    """
    Observability and latency tracking metrics container for real-time audio pipeline.
    """
    def __init__(self):
        self.sample_rate: int = 16000
        self.channels: int = 1
        self.sample_width: int = 2
        self.format_str: str = "pcm_s16le"
        self.total_chunks_received: int = 0
        self.total_bytes_received: int = 0
        self.total_duration_sec: float = 0.0
        self.speech_start_sec: Optional[float] = None
        self.speech_end_sec: Optional[float] = None
        self.asr_latency_ms: float = 0.0
        self.llm_latency_ms: float = 0.0
        self.tts_latency_ms: float = 0.0
        self.total_pipeline_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "sample_width": self.sample_width,
            "format": self.format_str,
            "chunks_received": self.total_chunks_received,
            "total_bytes": self.total_bytes_received,
            "duration_sec": round(self.total_duration_sec, 3),
            "speech_start_sec": round(self.speech_start_sec, 3) if self.speech_start_sec is not None else None,
            "speech_end_sec": round(self.speech_end_sec, 3) if self.speech_end_sec is not None else None,
            "asr_latency_ms": round(self.asr_latency_ms, 2),
            "llm_latency_ms": round(self.llm_latency_ms, 2),
            "tts_latency_ms": round(self.tts_latency_ms, 2),
            "total_pipeline_ms": round(self.total_pipeline_ms, 2)
        }


class RealtimeAudioPipeline:
    """
    Lesson 53 Real-Time Audio Pipeline:
    Manages audio capture format validation (16kHz 16-bit Mono PCM), streaming buffering,
    continuous VAD speech detection, endpointing state machine decisions, mic echo suppression,
    WAV formatting, and end-to-end audio pipeline metrics.
    """
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        sample_width: int = 2,
        part_mode: str = "part1",
        vad_engine: Optional[BaseVAD] = None
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.sample_width = sample_width
        self.buffer = AudioBuffer(sample_rate=sample_rate, channels=channels, sample_width=sample_width)
        self.turn_detector = TurnDetector(part_mode=part_mode, vad_engine=vad_engine)
        self.metrics = AudioPipelineMetrics()
        self.metrics.sample_rate = sample_rate
        self.metrics.channels = channels
        self.metrics.sample_width = sample_width
        self.examiner_speaking = False

    def set_examiner_speaking(self, is_speaking: bool) -> None:
        """
        Echo suppression guard: toggles whether examiner audio is active.
        When active, incoming candidate mic audio chunks are suppressed.
        """
        self.examiner_speaking = is_speaking

    def is_examiner_speaking(self) -> bool:
        return self.examiner_speaking

    def process_chunk(
        self,
        pcm_bytes: Optional[bytes] = None,
        float_samples: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Processes an incoming audio chunk (raw PCM bytes or Float32 samples from browser).
        Enforces echo suppression, appends audio to buffer, feeds VAD/TurnDetector,
        and returns step metadata.
        """
        if self.examiner_speaking:
            return {
                "echo_suppressed": True,
                "buffered_duration_sec": self.buffer.get_duration_seconds(),
                "turn_state": self.turn_detector.state.value,
                "is_finalized": False
            }

        if float_samples is not None:
            pcm_bytes = AudioBuffer.float32_to_pcm16(float_samples)

        if pcm_bytes:
            self.buffer.append_chunk(pcm_bytes)
            self.metrics.total_chunks_received = self.buffer.get_chunk_count()
            self.metrics.total_bytes_received = len(self.buffer.get_pcm_bytes())
            self.metrics.total_duration_sec = self.buffer.get_duration_seconds()

            # Process chunk through VAD & TurnDetector endpointing engine
            frame_ms = max(20, int((len(pcm_bytes) / (self.sample_rate * self.sample_width * self.channels)) * 1000))
            turn_res = self.turn_detector.process_frame(pcm_bytes, frame_duration_ms=frame_ms)

            # Update speech timestamps in metrics
            if turn_res.get("event_type") == "speech.started" and self.metrics.speech_start_sec is None:
                self.metrics.speech_start_sec = self.metrics.total_duration_sec
            if turn_res.get("event_type") == "speech.ended":
                self.metrics.speech_end_sec = self.metrics.total_duration_sec

            return {
                "echo_suppressed": False,
                "buffered_duration_sec": self.buffer.get_duration_seconds(),
                "turn_state": turn_res.get("state", self.turn_detector.state.value),
                "event_type": turn_res.get("event_type"),
                "is_finalized": turn_res.get("is_finalized", False),
                "end_reason": turn_res.get("end_reason"),
                "speech_prob": turn_res.get("speech_prob", 0.0)
            }

        return {
            "echo_suppressed": False,
            "buffered_duration_sec": self.buffer.get_duration_seconds(),
            "turn_state": self.turn_detector.state.value,
            "is_finalized": False
        }

    def export_turn_wav(self) -> bytes:
        """
        Exports accumulated audio buffer as a standard 16kHz 16-bit Mono WAV file.
        """
        return self.buffer.export_wav_bytes()

    def reset_turn(self) -> None:
        """
        Resets audio buffer and endpoint detector for the next candidate turn.
        """
        self.buffer.clear()
        self.turn_detector.reset()
        self.metrics.total_chunks_received = 0
        self.metrics.total_bytes_received = 0
        self.metrics.total_duration_sec = 0.0
        self.metrics.speech_start_sec = None
        self.metrics.speech_end_sec = None

    def get_metrics_dict(self) -> Dict[str, Any]:
        """
        Returns full observability metrics dictionary.
        """
        return self.metrics.to_dict()
