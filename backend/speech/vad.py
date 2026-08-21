from enum import Enum
import time
from typing import Optional, List, Dict, Any


class VADMode(str, Enum):
    PART1 = "part1"
    PART2 = "part2"
    PART3 = "part3"


class RealtimeSpeechState(str, Enum):
    IDLE = "idle"
    SPEAKING = "speaking"
    POSSIBLE_END = "possible_end"
    FINALIZED = "finalized"


class VADConfig:
    def __init__(
        self,
        mode: VADMode = VADMode.PART1,
        silence_threshold_sec: Optional[float] = None,
        sample_rate: int = 16000,
        bytes_per_sample: int = 2
    ):
        self.mode = mode
        self.sample_rate = sample_rate
        self.bytes_per_sample = bytes_per_sample
        
        # Configure mode-specific silence thresholds
        if silence_threshold_sec is not None:
            self.silence_threshold_sec = silence_threshold_sec
        elif mode == VADMode.PART1:
            self.silence_threshold_sec = 4.0
        elif mode == VADMode.PART2:
            self.silence_threshold_sec = 8.0
        elif mode == VADMode.PART3:
            self.silence_threshold_sec = 5.0
        else:
            self.silence_threshold_sec = 4.5


class RealtimeVADEngine:
    """
    Real-time Voice Activity Detection engine with mode-specific silence thresholds,
    rolling pre-speech audio buffer, and state tracking.
    """
    def __init__(self, config: Optional[VADConfig] = None):
        self.config = config or VADConfig()
        self.state = RealtimeSpeechState.IDLE
        self.rolling_buffer = bytearray()
        self.speech_buffer = bytearray()
        self.max_rolling_bytes = int(self.config.sample_rate * self.config.bytes_per_sample * 0.5) # 500ms pre-roll
        
        self.last_speech_time: Optional[float] = None
        self.speech_start_time: Optional[float] = None
        self.silence_start_time: Optional[float] = None
        self.examiner_speaking: bool = False

    def set_mode(self, mode: VADMode):
        self.config.mode = mode
        if mode == VADMode.PART1:
            self.config.silence_threshold_sec = 4.0
        elif mode == VADMode.PART2:
            self.config.silence_threshold_sec = 8.0
        elif mode == VADMode.PART3:
            self.config.silence_threshold_sec = 5.0

    def set_examiner_speaking(self, is_speaking: bool):
        """Sets feedback cancellation state to ignore microphone input while AI speaks."""
        self.examiner_speaking = is_speaking
        if is_speaking:
            # Reset current speech tracking during examiner speech
            self.reset_speech_segment()

    def is_energy_speech(self, chunk: bytes, energy_threshold: float = 300.0) -> bool:
        """
        Simple, fast PCM 16-bit RMS energy check for real-time frame classification.
        Can be backed by Silero VAD for full segment confirmation.
        """
        if not chunk or len(chunk) < 2:
            return False
        import struct
        samples_count = len(chunk) // 2
        if samples_count == 0:
            return False
        
        # Unpack signed 16-bit integers
        try:
            samples = struct.unpack(f"<{samples_count}h", chunk[:samples_count*2])
            abs_sum = sum(abs(s) for s in samples)
            avg_energy = abs_sum / samples_count
            return avg_energy > energy_threshold
        except Exception:
            return False

    def process_frame(self, frame: bytes) -> Dict[str, Any]:
        """
        Processes a single PCM audio frame (e.g. 20ms = 640 bytes).
        Returns status indicating state transition and whether a segment is finalized.
        """
        now = time.time()
        
        # Echo prevention check
        if self.examiner_speaking:
            return {
                "state": self.state,
                "is_finalized": False,
                "speech_audio": None,
                "ignored_reason": "examiner_speaking"
            }

        is_speech = self.is_energy_speech(frame)

        if not is_speech and self.state == RealtimeSpeechState.IDLE:
            # Maintain rolling buffer for pre-speech capture
            self.rolling_buffer.extend(frame)
            if len(self.rolling_buffer) > self.max_rolling_bytes:
                self.rolling_buffer = self.rolling_buffer[-self.max_rolling_bytes:]
            return {
                "state": RealtimeSpeechState.IDLE,
                "is_finalized": False,
                "speech_audio": None
            }

        if is_speech:
            if self.state == RealtimeSpeechState.IDLE:
                # Transition to SPEAKING with pre-speech pre-roll
                self.state = RealtimeSpeechState.SPEAKING
                self.speech_start_time = now
                self.speech_buffer = bytearray(self.rolling_buffer)
                self.speech_buffer.extend(frame)
                self.rolling_buffer.clear()
            else:
                self.speech_buffer.extend(frame)

            self.last_speech_time = now
            self.silence_start_time = None
            return {
                "state": RealtimeSpeechState.SPEAKING,
                "is_finalized": False,
                "speech_audio": None
            }

        else: # Silence detected while already in speech state
            if self.state in (RealtimeSpeechState.SPEAKING, RealtimeSpeechState.POSSIBLE_END):
                self.speech_buffer.extend(frame)
                if self.silence_start_time is None:
                    self.silence_start_time = now
                    self.state = RealtimeSpeechState.POSSIBLE_END
                
                silence_duration = now - self.silence_start_time
                if silence_duration >= self.config.silence_threshold_sec:
                    # Finalize utterance!
                    finalized_audio = bytes(self.speech_buffer)
                    self.state = RealtimeSpeechState.FINALIZED
                    
                    result = {
                        "state": RealtimeSpeechState.FINALIZED,
                        "is_finalized": True,
                        "speech_audio": finalized_audio,
                        "duration_sec": round(now - (self.speech_start_time or now), 2),
                        "silence_duration_sec": round(silence_duration, 2)
                    }
                    self.reset_speech_segment()
                    return result

                return {
                    "state": RealtimeSpeechState.POSSIBLE_END,
                    "is_finalized": False,
                    "speech_audio": None,
                    "silence_duration_sec": round(silence_duration, 2)
                }

        return {
            "state": self.state,
            "is_finalized": False,
            "speech_audio": None
        }

    def reset_speech_segment(self):
        self.state = RealtimeSpeechState.IDLE
        self.speech_buffer.clear()
        self.rolling_buffer.clear()
        self.speech_start_time = None
        self.last_speech_time = None
        self.silence_start_time = None
