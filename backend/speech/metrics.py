import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class LatencyMetrics:
    vad_time_ms: float = 0.0
    whisper_time_ms: float = 0.0
    qwen_time_ms: float = 0.0
    kokoro_time_ms: float = 0.0
    total_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "vad_ms": round(self.vad_time_ms, 2),
            "whisper_ms": round(self.whisper_time_ms, 2),
            "qwen_ms": round(self.qwen_time_ms, 2),
            "kokoro_ms": round(self.kokoro_time_ms, 2),
            "total_latency_ms": round(self.total_time_ms, 2)
        }


class PipelineLatencyTracker:
    def __init__(self):
        self.metrics = LatencyMetrics()
        self._start_times: Dict[str, float] = {}

    def start_stage(self, stage: str):
        self._start_times[stage] = time.perf_counter()

    def end_stage(self, stage: str) -> float:
        if stage in self._start_times:
            elapsed = (time.perf_counter() - self._start_times[stage]) * 1000.0
            if stage == "vad":
                self.metrics.vad_time_ms = elapsed
            elif stage == "whisper":
                self.metrics.whisper_time_ms = elapsed
            elif stage == "qwen":
                self.metrics.qwen_time_ms = elapsed
            elif stage == "kokoro":
                self.metrics.kokoro_time_ms = elapsed
            elif stage == "total":
                self.metrics.total_time_ms = elapsed
            return elapsed
        return 0.0

    def log_summary(self) -> str:
        d = self.metrics.to_dict()
        return (
            f"Latency Benchmark: Total={d['total_latency_ms']}ms | "
            f"VAD={d['vad_ms']}ms | Whisper={d['whisper_ms']}ms | "
            f"Qwen={d['qwen_ms']}ms | Kokoro={d['kokoro_ms']}ms"
        )
