import struct
import math
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional


class VADState(str, Enum):
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    SPEECH_DETECTED = "SPEECH_DETECTED"
    IN_SPEECH = "IN_SPEECH"
    POSSIBLE_END = "POSSIBLE_END"
    SPEECH_COMPLETE = "SPEECH_COMPLETE"


class BaseVAD(ABC):
    """
    Abstract Base Class for Voice Activity Detection implementations.
    """

    @abstractmethod
    def get_speech_probability(self, pcm_chunk: bytes) -> float:
        """
        Returns speech probability between 0.0 (silence) and 1.0 (speech).
        """
        pass

    def is_speech(self, pcm_chunk: bytes, threshold: float = 0.5) -> bool:
        """
        Returns True if speech probability exceeds threshold.
        """
        return self.get_speech_probability(pcm_chunk) >= threshold


class EnergyVAD(BaseVAD):
    """
    Lightweight Energy/RMS-based VAD for 16kHz 16-bit Mono PCM audio.
    Calculates root-mean-square amplitude and maps energy to speech probability.
    """

    def __init__(self, energy_threshold: float = 300.0, max_energy: float = 3000.0):
        self.energy_threshold = energy_threshold
        self.max_energy = max_energy

    def calculate_rms(self, pcm_chunk: bytes) -> float:
        if not pcm_chunk or len(pcm_chunk) < 2:
            return 0.0
        sample_count = len(pcm_chunk) // 2
        try:
            samples = struct.unpack(f"<{sample_count}h", pcm_chunk[:sample_count * 2])
            sum_squares = sum(s * s for s in samples)
            rms = math.sqrt(sum_squares / sample_count)
            return rms
        except Exception:
            return 0.0

    def get_speech_probability(self, pcm_chunk: bytes) -> float:
        rms = self.calculate_rms(pcm_chunk)
        if rms < self.energy_threshold:
            # Scale linearly between 0 and 0.4
            return max(0.0, (rms / self.energy_threshold) * 0.4)
        else:
            # Scale between 0.5 and 1.0
            prob = 0.5 + 0.5 * min(1.0, (rms - self.energy_threshold) / (self.max_energy - self.energy_threshold))
            return min(1.0, prob)


class SileroVAD(BaseVAD):
    """
    Neural Silero VAD Wrapper with deterministic EnergyVAD fallback.
    Executes CPU-friendly speech detection for 16kHz PCM frames.
    """

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        self.fallback = EnergyVAD()
        self.model = None
        self._init_silero()

    def _init_silero(self):
        try:
            import torch
            # Attempt loading Silero VAD torch model if installed locally
            model, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )
            self.model = model
            print("[SileroVAD] Loaded Silero VAD neural model successfully.")
        except Exception as e:
            print(f"[SileroVAD] Torch/Silero model unavailable ({e}). Using CPU EnergyVAD fallback.")
            self.model = None

    def get_speech_probability(self, pcm_chunk: bytes) -> float:
        if self.model is not None:
            try:
                import torch
                # Convert 16-bit PCM to normalized Float32 tensor
                sample_count = len(pcm_chunk) // 2
                if sample_count == 0:
                    return 0.0
                samples = struct.unpack(f"<{sample_count}h", pcm_chunk[:sample_count * 2])
                tensor = torch.tensor([s / 32768.0 for s in samples], dtype=torch.float32)
                
                with torch.no_grad():
                    prob = self.model(tensor, 16000).item()
                    return float(prob)
            except Exception as e:
                return self.fallback.get_speech_probability(pcm_chunk)
        return self.fallback.get_speech_probability(pcm_chunk)


class VADSegmenter:
    """
    Stateful VAD Endpointing & Speech Segmenter.
    Combines VAD probabilities, pre-roll buffer, post-roll buffer,
    silence tolerance, and minimum speech duration thresholds into a complete
    speech segment detector for IELTS candidate answers.
    """

    def __init__(
        self,
        vad_engine: Optional[BaseVAD] = None,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30,  # 30ms audio frames (960 bytes for 16kHz 16bit)
        pre_roll_ms: int = 300,
        post_roll_ms: int = 300,
        min_speech_ms: int = 300,
        silence_threshold_ms: int = 1200,  # Part 1 default: 1.2s
        speech_prob_threshold: float = 0.5
    ):
        self.vad = vad_engine or EnergyVAD()
        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.pre_roll_ms = pre_roll_ms
        self.post_roll_ms = post_roll_ms
        self.min_speech_ms = min_speech_ms
        self.silence_threshold_ms = silence_threshold_ms
        self.speech_prob_threshold = speech_prob_threshold

        # Buffers
        self.max_pre_roll_chunks = max(1, pre_roll_ms // frame_duration_ms)
        self.max_post_roll_chunks = max(1, post_roll_ms // frame_duration_ms)
        self._pre_roll_buffer: List[bytes] = []
        self._speech_buffer: List[bytes] = []
        self._post_roll_buffer: List[bytes] = []

        # State tracking
        self.state = VADState.IDLE
        self.speech_duration_ms = 0
        self.silence_duration_ms = 0

    def set_ielts_mode(self, mode: str):
        """
        Sets endpoint silence tolerance threshold based on IELTS Part context.
        - Part 1: 1200 ms (short concise answers)
        - Part 2: 2000 ms (long turn pauses)
        - Part 3: 1500 ms (analytical answers)
        """
        mode_lower = mode.lower()
        if "part2" in mode_lower:
            self.silence_threshold_ms = 2000
        elif "part3" in mode_lower:
            self.silence_threshold_ms = 1500
        else:
            self.silence_threshold_ms = 1200

    def process_frame(self, pcm_chunk: bytes) -> Dict[str, Any]:
        """
        Processes a raw PCM audio chunk through the VAD state machine.
        Returns a dict containing state, speech probability, and finalized audio segment if complete.
        """
        prob = self.vad.get_speech_probability(pcm_chunk)
        is_speech = prob >= self.speech_prob_threshold

        if self.state == VADState.IDLE or self.state == VADState.LISTENING:
            if not is_speech:
                # Accumulate pre-roll buffer
                self._pre_roll_buffer.append(pcm_chunk)
                if len(self._pre_roll_buffer) > self.max_pre_roll_chunks:
                    self._pre_roll_buffer.pop(0)
                self.state = VADState.LISTENING
                return {
                    "state": self.state.value,
                    "is_speech": False,
                    "speech_probability": round(prob, 3),
                    "is_finalized": False,
                    "audio": None,
                    "duration_sec": 0.0
                }
            else:
                # Speech detected!
                self.speech_duration_ms += self.frame_duration_ms
                self.silence_duration_ms = 0
                
                # Prepend pre-roll buffer to speech buffer
                self._speech_buffer = list(self._pre_roll_buffer)
                self._speech_buffer.append(pcm_chunk)
                self._pre_roll_buffer.clear()

                if self.speech_duration_ms >= self.min_speech_ms:
                    self.state = VADState.IN_SPEECH
                else:
                    self.state = VADState.SPEECH_DETECTED

                return {
                    "state": self.state.value,
                    "is_speech": True,
                    "speech_probability": round(prob, 3),
                    "is_finalized": False,
                    "audio": None,
                    "duration_sec": round((len(self._speech_buffer) * self.frame_duration_ms) / 1000.0, 3)
                }

        elif self.state in (VADState.SPEECH_DETECTED, VADState.IN_SPEECH, VADState.POSSIBLE_END):
            if is_speech:
                # Speech continues or resumes after brief pause
                self.speech_duration_ms += self.frame_duration_ms
                self.silence_duration_ms = 0
                
                # Flush any post-roll frames into speech buffer
                if self._post_roll_buffer:
                    self._speech_buffer.extend(self._post_roll_buffer)
                    self._post_roll_buffer.clear()

                self._speech_buffer.append(pcm_chunk)
                self.state = VADState.IN_SPEECH

                return {
                    "state": self.state.value,
                    "is_speech": True,
                    "speech_probability": round(prob, 3),
                    "is_finalized": False,
                    "audio": None,
                    "duration_sec": round((len(self._speech_buffer) * self.frame_duration_ms) / 1000.0, 3)
                }
            else:
                # Silence during speech turn
                self.silence_duration_ms += self.frame_duration_ms
                self._post_roll_buffer.append(pcm_chunk)

                if self.silence_duration_ms >= self.silence_threshold_ms:
                    # Endpoint reached! Candidate finished speaking
                    # Include post-roll buffer (up to max_post_roll_chunks)
                    post_roll_to_add = self._post_roll_buffer[:self.max_post_roll_chunks]
                    complete_pcm = b"".join(self._speech_buffer + post_roll_to_add)
                    total_duration = round((len(complete_pcm) / (self.sample_rate * 2)), 3)

                    self.state = VADState.SPEECH_COMPLETE
                    result = {
                        "state": self.state.value,
                        "is_speech": False,
                        "speech_probability": round(prob, 3),
                        "is_finalized": True,
                        "audio": complete_pcm,
                        "duration_sec": total_duration,
                        "silence_ms": self.silence_duration_ms
                    }
                    self.reset()
                    return result
                else:
                    self.state = VADState.POSSIBLE_END
                    return {
                        "state": self.state.value,
                        "is_speech": False,
                        "speech_probability": round(prob, 3),
                        "is_finalized": False,
                        "audio": None,
                        "silence_ms": self.silence_duration_ms,
                        "duration_sec": round((len(self._speech_buffer) * self.frame_duration_ms) / 1000.0, 3)
                    }

        return {
            "state": self.state.value,
            "is_speech": False,
            "speech_probability": round(prob, 3),
            "is_finalized": False,
            "audio": None,
            "duration_sec": 0.0
        }

    def reset(self):
        """
        Resets VAD segmenter state and buffers.
        """
        self.state = VADState.IDLE
        self.speech_duration_ms = 0
        self.silence_duration_ms = 0
        self._pre_roll_buffer.clear()
        self._speech_buffer.clear()
        self._post_roll_buffer.clear()
