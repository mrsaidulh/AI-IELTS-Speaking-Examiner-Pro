import time
from typing import Dict, Any, Optional
from speech_config import SpeechConfig, VADMode, SETTINGS
from audio_buffer import RollingBuffer


class VADEngine:
    """
    Voice Activity Detection Engine with mode-specific silence thresholds,
    rolling pre-speech buffer, and state tracking for IELTS Speaking.
    """
    def __init__(self, mode: str = VADMode.PART1):
        self.config = SpeechConfig()
        self.mode = mode
        self.settings = SETTINGS.get(mode, SETTINGS["part1"])
        self.end_silence_ms = self.settings["end_silence_ms"]
        
        self.is_speaking = False
        self.silence_ms = 0
        self.speech_ms = 0
        self.rolling_buffer = RollingBuffer(max_frames=int(self.config.PRE_ROLL_MS / self.config.FRAME_DURATION_MS))
        self.speech_frames = []
        self.speech_start_time: Optional[float] = None
        self.last_speech_time: Optional[float] = None

    def set_mode(self, mode: str):
        self.mode = mode
        self.settings = SETTINGS.get(mode, SETTINGS["part1"])
        self.end_silence_ms = self.settings["end_silence_ms"]

    def is_energy_speech(self, frame: bytes, threshold: float = 300.0) -> bool:
        if not frame or len(frame) < 2:
            return False
        import struct
        samples_count = len(frame) // 2
        if samples_count == 0:
            return False
        try:
            samples = struct.unpack(f"<{samples_count}h", frame[:samples_count*2])
            avg_energy = sum(abs(s) for s in samples) / samples_count
            return avg_energy > threshold
        except Exception:
            return False

    def process_frame(self, frame: bytes) -> Dict[str, Any]:
        now = time.time()
        is_speech = self.is_energy_speech(frame)

        if not is_speech and not self.is_speaking:
            self.rolling_buffer.add(frame)
            return {
                "state": "IDLE",
                "is_finalized": False,
                "audio": None
            }

        if is_speech:
            self.speech_ms += self.config.FRAME_DURATION_MS
            self.silence_ms = 0
            self.last_speech_time = now

            if not self.is_speaking:
                if self.speech_ms >= self.config.MIN_SPEECH_MS:
                    self.is_speaking = True
                    self.speech_start_time = now - (self.speech_ms / 1000.0)
                    # Include pre-roll buffer
                    self.speech_frames = self.rolling_buffer.get()
                    self.speech_frames.append(frame)
                    self.rolling_buffer.clear()
            else:
                self.speech_frames.append(frame)

            return {
                "state": "SPEAKING",
                "is_finalized": False,
                "audio": None
            }
        else:
            # Silence during speech
            if self.is_speaking:
                self.speech_frames.append(frame)
                self.silence_ms += self.config.FRAME_DURATION_MS

                if self.silence_ms >= self.end_silence_ms:
                    # Answer finalized
                    complete_audio = b"".join(self.speech_frames)
                    duration_sec = round(now - (self.speech_start_time or now), 2)
                    
                    self.reset()
                    return {
                        "state": "FINALIZED",
                        "is_finalized": True,
                        "audio": complete_audio,
                        "duration_sec": duration_sec,
                        "silence_ms": self.silence_ms
                    }

                return {
                    "state": "POSSIBLE_END",
                    "is_finalized": False,
                    "audio": None,
                    "silence_ms": self.silence_ms
                }

        return {
            "state": "IDLE",
            "is_finalized": False,
            "audio": None
        }

    def reset(self):
        self.is_speaking = False
        self.silence_ms = 0
        self.speech_ms = 0
        self.rolling_buffer.clear()
        self.speech_frames = []
        self.speech_start_time = None
        self.last_speech_time = None
