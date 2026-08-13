import json
from typing import List, Dict, Any

try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    from dataclasses import dataclass, field, asdict


if PYDANTIC_AVAILABLE:
    class TranscriptSegment(BaseModel):
        start: float = Field(..., description="Start timestamp in seconds")
        end: float = Field(..., description="End timestamp in seconds")
        text: str = Field(..., description="Transcribed segment text")

        def model_dump(self) -> Dict[str, Any]:
            return self.dict() if hasattr(self, "dict") else super().model_dump()


    class Transcript(BaseModel):
        text: str = Field(..., description="Full concatenated transcript text")
        language: str = Field("en", description="Detected or specified ISO language code")
        segments: List[TranscriptSegment] = Field(default_factory=list, description="List of granular timestamped segments")
        language_probability: float = Field(1.0, description="Confidence score for detected language")
        processing_time_sec: float = Field(0.0, description="Transcription latency in seconds")
        rtf: float = Field(0.0, description="Real-Time Factor (processing_time / audio_duration)")
        is_partial: bool = Field(False, description="Flag indicating if transcript is temporary/partial or final")

        def model_dump(self) -> Dict[str, Any]:
            if hasattr(super(), "model_dump"):
                res = super().model_dump()
            else:
                res = {
                    "text": self.text,
                    "language": self.language,
                    "segments": [s.model_dump() for s in self.segments],
                    "language_probability": self.language_probability,
                    "processing_time_sec": self.processing_time_sec,
                    "rtf": self.rtf,
                    "is_partial": self.is_partial
                }
            return res

        def model_dump_json(self, indent: int = 2) -> str:
            return json.dumps(self.model_dump(), indent=indent)


    class SpeakingTurn(BaseModel):
        id: str = Field(..., description="Unique turn identifier")
        session_id: str = Field(..., description="Session identifier")
        turn_number: int = Field(1, description="Sequential candidate turn number")
        start_time: float = Field(0.0, description="Start timestamp")
        end_time: float = Field(0.0, description="End timestamp")
        duration_sec: float = Field(0.0, description="Turn audio duration in seconds")
        partial_transcripts: List[str] = Field(default_factory=list, description="Accumulated partial transcripts")
        final_transcript: str = Field("", description="Final authoritative candidate transcript")
        examiner_question: str = Field("", description="Examiner question prompt")
        examiner_response: str = Field("", description="Generated examiner text response")
        latency_metrics: Dict[str, float] = Field(default_factory=dict, description="Latency breakdown metrics")

        def model_dump(self) -> Dict[str, Any]:
            if hasattr(super(), "model_dump"):
                return super().model_dump()
            return self.dict()

else:
    @dataclass
    class TranscriptSegment:
        start: float
        end: float
        text: str

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

        def dict(self) -> Dict[str, Any]:
            return asdict(self)


    @dataclass
    class Transcript:
        text: str
        language: str = "en"
        segments: List[TranscriptSegment] = field(default_factory=list)
        language_probability: float = 1.0
        processing_time_sec: float = 0.0
        rtf: float = 0.0
        is_partial: bool = False

        def model_dump(self) -> Dict[str, Any]:
            return {
                "text": self.text,
                "language": self.language,
                "segments": [s.model_dump() for s in self.segments],
                "language_probability": self.language_probability,
                "processing_time_sec": self.processing_time_sec,
                "rtf": self.rtf,
                "is_partial": self.is_partial
            }

        def dict(self) -> Dict[str, Any]:
            return self.model_dump()

        def model_dump_json(self, indent: int = 2) -> str:
            return json.dumps(self.model_dump(), indent=indent)


    @dataclass
    class SpeakingTurn:
        id: str
        session_id: str
        turn_number: int = 1
        start_time: float = 0.0
        end_time: float = 0.0
        duration_sec: float = 0.0
        partial_transcripts: List[str] = field(default_factory=list)
        final_transcript: str = ""
        examiner_question: str = ""
        examiner_response: str = ""
        latency_metrics: Dict[str, float] = field(default_factory=dict)

        def model_dump(self) -> Dict[str, Any]:
            return asdict(self)

        def dict(self) -> Dict[str, Any]:
            return asdict(self)

