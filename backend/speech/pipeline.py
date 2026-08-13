import logging
import time
import uuid
from typing import Dict, Any, Optional, List
from speech.vad import RealtimeVADEngine, VADMode, VADConfig, RealtimeSpeechState
from speech.metrics import PipelineLatencyTracker
from speech.queue_worker import RealtimeVoiceQueueWorker
from speech.whisper_service import WhisperService
from speech.kokoro_service import KokoroService, KokoroAudioResult
from speech.schema import SpeakingTurn, Transcript
from qwen_service import QwenService
from examiner.controller import ExaminerController
from examiner.actions import ExaminerAction
from audio.buffer import AudioBuffer
from audio.turn_detector import TurnDetector
from websocket.protocol import WebSocketState, WebSocketEventType, format_ws_event, format_state_event

logger = logging.getLogger("speech_pipeline")


class RealtimeVoiceOrchestrator:
    """
    Lesson 50 Core Orchestrator:
    Connects Microphone VAD Endpointing -> Whisper ASR -> Examiner Controller (Qwen) -> Kokoro TTS
    into a single unified, event-driven real-time voice pipeline.
    """
    def __init__(
        self,
        session_id: str,
        whisper_service: Optional[WhisperService] = None,
        qwen_service: Optional[QwenService] = None,
        kokoro_service: Optional[KokoroService] = None,
        controller: Optional[ExaminerController] = None
    ):
        self.session_id = session_id
        self.whisper = whisper_service or WhisperService()
        self.qwen = qwen_service or QwenService()
        self.kokoro = kokoro_service or KokoroService()
        self.controller = controller or ExaminerController(session_id=session_id)
        
        self.audio_buffer = AudioBuffer(sample_rate=16000, channels=1, sample_width=2)
        self.turn_detector = TurnDetector(part_mode=self.controller.part.value)
        self.latency_tracker = PipelineLatencyTracker()
        
        self.turns: List[SpeakingTurn] = []
        self.current_turn_number = 0
        self.examiner_speaking = False
        self.state = WebSocketState.READY

    def set_examiner_speaking(self, is_speaking: bool):
        """Echo suppression toggle flag."""
        self.examiner_speaking = is_speaking

    def is_examiner_speaking(self) -> bool:
        return self.examiner_speaking

    async def execute_voice_turn(
        self,
        candidate_audio_bytes: bytes,
        examiner_question_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a complete end-to-end voice-to-voice turn:
        1. Final ASR via Whisper
        2. Examiner reasoning via Qwen Controller
        3. Speech synthesis via Kokoro TTS
        4. Structured SpeakingTurn generation & latency benchmark tracking
        """
        self.latency_tracker = PipelineLatencyTracker()
        self.latency_tracker.start_stage("total")
        
        # 1. ASR Stage (Whisper)
        self.latency_tracker.start_stage("whisper")
        transcript_obj: Transcript = self.whisper.transcribe_final(candidate_audio_bytes, language="en")
        asr_time_ms = self.latency_tracker.end_stage("whisper")

        candidate_text = transcript_obj.text.strip()
        current_question = examiner_question_override or self.controller.get_current_question_info().get("question", "")

        # 2. LLM Reasoning Stage (Examiner Controller + Qwen)
        self.latency_tracker.start_stage("qwen")
        turn_res = self.controller.process_candidate_turn(
            candidate_answer=candidate_text,
            qwen_service=self.qwen
        )
        qwen_time_ms = self.latency_tracker.end_stage("qwen")

        examiner_text = turn_res.get("examiner_response", "")

        # 3. TTS Stage (Kokoro)
        self.latency_tracker.start_stage("kokoro")
        audio_res: KokoroAudioResult = self.kokoro.synthesize(examiner_text)
        kokoro_time_ms = self.latency_tracker.end_stage("kokoro")

        total_time_ms = self.latency_tracker.end_stage("total")

        # 4. Construct SpeakingTurn object
        self.current_turn_number += 1
        turn_obj = SpeakingTurn(
            id=f"turn_{self.current_turn_number:03d}_{uuid.uuid4().hex[:6]}",
            session_id=self.session_id,
            turn_number=self.current_turn_number,
            start_time=time.time() - (len(candidate_audio_bytes) / 32000.0),
            end_time=time.time(),
            duration_sec=round(len(candidate_audio_bytes) / 32000.0, 3),
            final_transcript=candidate_text,
            examiner_question=current_question,
            examiner_response=examiner_text,
            latency_metrics={
                "asr_ms": round(asr_time_ms, 2),
                "qwen_ms": round(qwen_time_ms, 2),
                "tts_ms": round(kokoro_time_ms, 2),
                "total_ms": round(total_time_ms, 2)
            }
        )
        self.turns.append(turn_obj)

        return {
            "turn_id": turn_obj.id,
            "turn_number": turn_obj.turn_number,
            "candidate_transcript": candidate_text,
            "examiner_response": examiner_text,
            "action": turn_res.get("action", ExaminerAction.ASK_NEXT.value),
            "current_part": turn_res.get("current_part", self.controller.part.value),
            "audio_base64": audio_res.audio_base64,
            "audio_duration_sec": audio_res.duration_sec,
            "tts_cached": audio_res.cached,
            "latency_metrics": turn_obj.latency_metrics,
            "summary": self.latency_tracker.log_summary()
        }


class FullDuplexVoicePipeline:
    """
    Full-duplex Real-Time Voice Pipeline orchestrator for IELTS Speaking AI.
    Handles PCM audio stream ingestion, echo prevention, VAD segmentation,
    and non-blocking asynchronous speech processing.
    """
    def __init__(self, mode: VADMode = VADMode.PART1):
        self.vad = RealtimeVADEngine(VADConfig(mode=mode))
        self.queue_worker = RealtimeVoiceQueueWorker(max_queue_size=10)
        self.examiner_speaking = False

    def set_mode(self, mode: VADMode):
        """Sets VAD mode (PART1, PART2, or PART3) to adjust silence thresholds."""
        self.vad.set_mode(mode)

    def set_examiner_speaking(self, is_speaking: bool):
        """Toggles echo-prevention flag when examiner AI is generating/playing TTS audio."""
        self.examiner_speaking = is_speaking
        self.vad.set_examiner_speaking(is_speaking)

    def process_pcm_frame(self, frame: bytes) -> Dict[str, Any]:
        """
        Process incoming 16kHz 16-bit mono PCM chunk from WebSocket stream.
        """
        return self.vad.process_frame(frame)
