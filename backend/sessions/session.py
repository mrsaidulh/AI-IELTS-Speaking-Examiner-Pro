import time
from typing import List, Dict, Any, Optional
from vad import VADEngine
from speech_config import VADMode


class SpeakingSession:
    """
    Encapsulates state, timers, and VAD processing for a specific candidate's IELTS Speaking test.
    """
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.part = 1
        self.question_number = 1
        self.question = "Can you tell me your full name?"
        
        self.is_speaking = False
        self.examiner_speaking = False
        self.silence_ms = 0
        self.audio_frames = []
        
        self.started_at = time.time()
        self.preparation_time = 0
        self.speaking_time = 0
        
        self.vad_engine = VADEngine(mode=VADMode.PART1)
        self.transcript_history: List[Dict[str, Any]] = []

    def set_part(self, part: int):
        self.part = part
        if part == 1:
            self.vad_engine.set_mode(VADMode.PART1)
        elif part == 2:
            self.vad_engine.set_mode(VADMode.PART2)
        elif part == 3:
            self.vad_engine.set_mode(VADMode.PART3)

    def set_examiner_speaking(self, is_speaking: bool):
        self.examiner_speaking = is_speaking
        if is_speaking:
            self.vad_engine.reset()

    def process_audio_chunk(self, chunk: bytes) -> Dict[str, Any]:
        if self.examiner_speaking:
            return {
                "state": "EXAMINER_SPEAKING",
                "is_finalized": False,
                "audio": None
            }

        res = self.vad_engine.process_frame(chunk)
        self.is_speaking = self.vad_engine.is_speaking
        self.silence_ms = self.vad_engine.silence_ms
        return res
