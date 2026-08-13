import time
from enum import Enum
from typing import Dict, Any, Optional, List
from audio.vad import BaseVAD, EnergyVAD


class TurnState(str, Enum):
    """
    Candidate speech turn state machine states.
    """
    IDLE = "IDLE"
    LISTENING = "LISTENING"
    CANDIDATE_SPEAKING = "CANDIDATE_SPEAKING"
    POSSIBLE_END = "POSSIBLE_END"
    TURN_ENDED = "TURN_ENDED"


class TurnDetector:
    """
    Stateful Speech Endpointing & Conversation Turn Detection Engine.
    
    Coordinates VAD frames, pause/resumption state tracking, dynamic IELTS Part
    endpoint silence thresholds (Part 1: 1.2s, Part 2: 2.0s, Part 3: 1.5s),
    hard max response timeouts, noise filtering, and timestamped transition logging.
    """

    def __init__(
        self,
        part_mode: str = "part1",
        vad_engine: Optional[BaseVAD] = None,
        min_speech_ms: int = 300,
        speech_prob_threshold: float = 0.5
    ):
        self.vad = vad_engine or EnergyVAD()
        self.min_speech_ms = min_speech_ms
        self.speech_prob_threshold = speech_prob_threshold
        
        self.state = TurnState.IDLE
        self.part_mode = "part1"
        self.silence_threshold_ms = 1200
        self.max_duration_sec = 60.0

        self.speech_duration_ms = 0
        self.silence_duration_ms = 0
        self.accumulated_speech_ms = 0
        self.total_turn_duration_sec = 0.0

        self.logs: List[Dict[str, Any]] = []
        self.set_part_mode(part_mode)

    def set_part_mode(self, mode: Any):
        """
        Configures dynamic endpoint silence threshold and max duration timeout
        based on current IELTS Speaking Part.
        - Part 1: 1200ms silence tolerance, 60s max duration
        - Part 2: 2000ms silence tolerance, 120s max duration (Long turn)
        - Part 3: 1500ms silence tolerance, 90s max duration
        """
        mode_str = str(mode).lower()
        self.part_mode = mode_str
        if "part2" in mode_str or mode_str == "2":
            self.silence_threshold_ms = 2000
            self.max_duration_sec = 120.0
        elif "part3" in mode_str or mode_str == "3":
            self.silence_threshold_ms = 1500
            self.max_duration_sec = 90.0
        else:
            self.silence_threshold_ms = 1200
            self.max_duration_sec = 60.0

    def _log_event(self, event_name: str, details: Optional[Dict[str, Any]] = None):
        """
        Records a timestamped state transition log for latency and turn debugging.
        """
        now = time.strftime("%H:%M:%S") + f".{int((time.time() % 1) * 1000):03d}"
        log_entry = {
            "timestamp": now,
            "event": event_name,
            "state": self.state.value,
            "part_mode": self.part_mode,
            "details": details or {}
        }
        self.logs.append(log_entry)
        print(f"[{now}] TurnDetector | {event_name} | State={self.state.value} | {details or ''}")

    def process_frame(
        self,
        pcm_chunk: bytes,
        frame_duration_ms: int = 20
    ) -> Dict[str, Any]:
        """
        Processes a raw PCM audio chunk through the Turn Detector state machine.
        Returns a dict containing the current state, event_type (if state changed),
        speech probability, and whether turn is finalized.
        """
        prob = self.vad.get_speech_probability(pcm_chunk)
        is_speech = prob >= self.speech_prob_threshold
        event_type: Optional[str] = None
        is_finalized = False
        end_reason: Optional[str] = None

        if self.state in (TurnState.IDLE, TurnState.LISTENING):
            if is_speech:
                self.accumulated_speech_ms += frame_duration_ms
                if self.accumulated_speech_ms >= self.min_speech_ms:
                    # Noise guard passed! Candidate turn started
                    self.state = TurnState.CANDIDATE_SPEAKING
                    self.speech_duration_ms = self.accumulated_speech_ms
                    self.silence_duration_ms = 0
                    self.total_turn_duration_sec = self.speech_duration_ms / 1000.0
                    event_type = "speech.started"
                    self._log_event(event_type, {"speech_prob": round(prob, 3)})
                else:
                    self.state = TurnState.LISTENING
            else:
                self.accumulated_speech_ms = 0
                self.state = TurnState.LISTENING

        elif self.state == TurnState.CANDIDATE_SPEAKING:
            self.total_turn_duration_sec = round(self.total_turn_duration_sec + frame_duration_ms / 1000.0, 4)
            
            # Check hard maximum duration timer first
            if round(self.total_turn_duration_sec, 2) >= self.max_duration_sec:
                self.state = TurnState.TURN_ENDED
                is_finalized = True
                end_reason = "max_duration_exceeded"
                event_type = "speech.ended"
                self._log_event(event_type, {
                    "reason": end_reason,
                    "duration_sec": round(self.total_turn_duration_sec, 2)
                })
            elif not is_speech:
                # Speech paused -> check if silence immediately exceeds threshold or enters POSSIBLE_END
                self.silence_duration_ms += frame_duration_ms
                if self.silence_duration_ms >= self.silence_threshold_ms:
                    self.state = TurnState.TURN_ENDED
                    is_finalized = True
                    end_reason = "silence_timeout"
                    event_type = "speech.ended"
                    self._log_event(event_type, {
                        "reason": end_reason,
                        "silence_ms": self.silence_duration_ms,
                        "total_duration_sec": round(self.total_turn_duration_sec, 2)
                    })
                else:
                    self.state = TurnState.POSSIBLE_END
                    event_type = "speech.possible_end"
                    self._log_event(event_type, {"silence_ms": self.silence_duration_ms})
            else:
                # Speech continues
                self.speech_duration_ms += frame_duration_ms
                self.silence_duration_ms = 0

        elif self.state == TurnState.POSSIBLE_END:
            self.total_turn_duration_sec = round(self.total_turn_duration_sec + frame_duration_ms / 1000.0, 4)
            
            if round(self.total_turn_duration_sec, 2) >= self.max_duration_sec:
                self.state = TurnState.TURN_ENDED
                is_finalized = True
                end_reason = "max_duration_exceeded"
                event_type = "speech.ended"
                self._log_event(event_type, {
                    "reason": end_reason,
                    "duration_sec": round(self.total_turn_duration_sec, 2)
                })
            elif is_speech:
                # Speech resumed before silence threshold reached!
                self.speech_duration_ms += frame_duration_ms
                self.silence_duration_ms = 0
                self.state = TurnState.CANDIDATE_SPEAKING
                event_type = "speech.resumed"
                self._log_event(event_type, {"speech_prob": round(prob, 3)})
            else:
                # Silence continues
                self.silence_duration_ms += frame_duration_ms
                
                # Check silence threshold timeout
                if self.silence_duration_ms >= self.silence_threshold_ms:
                    self.state = TurnState.TURN_ENDED
                    is_finalized = True
                    end_reason = "silence_timeout"
                    event_type = "speech.ended"
                    self._log_event(event_type, {
                        "reason": end_reason,
                        "silence_ms": self.silence_duration_ms,
                        "total_duration_sec": round(self.total_turn_duration_sec, 2)
                    })

        return {
            "state": self.state.value,
            "event_type": event_type,
            "is_speech": is_speech,
            "speech_probability": round(prob, 3),
            "is_finalized": is_finalized,
            "end_reason": end_reason,
            "silence_ms": self.silence_duration_ms,
            "speech_duration_ms": self.speech_duration_ms,
            "total_duration_sec": round(self.total_turn_duration_sec, 3),
            "silence_threshold_ms": self.silence_threshold_ms,
            "max_duration_sec": self.max_duration_sec,
            "part_mode": self.part_mode
        }

    def reset(self):
        """
        Resets the turn detector state and counters for a new candidate turn.
        """
        self.state = TurnState.IDLE
        self.speech_duration_ms = 0
        self.silence_duration_ms = 0
        self.accumulated_speech_ms = 0
        self.total_turn_duration_sec = 0.0

    def get_logs(self) -> List[Dict[str, Any]]:
        return list(self.logs)
