import json
import asyncio
from typing import Dict, Any, Optional

try:
    from fastapi import WebSocket, WebSocketDisconnect
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    class WebSocketDisconnect(Exception):
        pass
    class WebSocket:
        pass

from websocket.protocol import (
    WebSocketState,
    WebSocketEventType,
    format_ws_event,
    format_state_event,
    format_error_event
)
from examiner.controller import ExaminerController
from examiner.actions import ExaminerAction
from qwen_service import QwenService
from speech.whisper_service import WhisperService
from speech.kokoro_service import KokoroService
from speech.metrics import PipelineLatencyTracker
from audio.buffer import AudioBuffer
from audio.vad import VADSegmenter, EnergyVAD, VADState
from audio.turn_detector import TurnDetector


class WebSocketManager:
    """
    Manages active WebSocket connections per session_id, ensuring
    candidate state isolation, server-authoritative state tracking,
    session audio buffering, real-time VAD, TurnDetector endpointing,
    Whisper ASR transcription, and Kokoro TTS audio generation.
    """
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.controllers: Dict[str, ExaminerController] = {}
        self.qwen_services: Dict[str, QwenService] = {}
        self.whisper_services: Dict[str, WhisperService] = {}
        self.kokoro_services: Dict[str, KokoroService] = {}
        self.orchestrators: Dict[str, Any] = {}
        self.audio_buffers: Dict[str, AudioBuffer] = {}
        self.vad_segmenters: Dict[str, VADSegmenter] = {}
        self.turn_detectors: Dict[str, TurnDetector] = {}
        self.examiner_speaking_states: Dict[str, bool] = {}

    def set_examiner_speaking(self, session_id: str, is_speaking: bool):
        self.examiner_speaking_states[session_id] = is_speaking

    def is_examiner_speaking(self, session_id: str) -> bool:
        return self.examiner_speaking_states.get(session_id, False)

    async def connect(self, session_id: str, websocket: WebSocket) -> ExaminerController:
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        if session_id not in self.controllers:
            from speech.pipeline import RealtimeVoiceOrchestrator
            ctrl = ExaminerController(session_id=session_id)
            qwen = QwenService()
            whisper = WhisperService()
            kokoro = KokoroService()
            
            self.controllers[session_id] = ctrl
            self.qwen_services[session_id] = qwen
            self.whisper_services[session_id] = whisper
            self.kokoro_services[session_id] = kokoro
            self.orchestrators[session_id] = RealtimeVoiceOrchestrator(
                session_id=session_id,
                whisper_service=whisper,
                qwen_service=qwen,
                kokoro_service=kokoro,
                controller=ctrl
            )
            self.examiner_speaking_states[session_id] = False
            self.audio_buffers[session_id] = AudioBuffer(sample_rate=16000, channels=1, sample_width=2)
            self.vad_segmenters[session_id] = VADSegmenter(
                vad_engine=EnergyVAD(),
                sample_rate=16000,
                pre_roll_ms=300,
                post_roll_ms=300,
                min_speech_ms=300,
                silence_threshold_ms=1200
            )
            self.turn_detectors[session_id] = TurnDetector(
                part_mode=ctrl.part.value
            )

        # Send initial connected and session_ready events
        await self.send_event(session_id, format_state_event(WebSocketState.CONNECTED))
        return self.controllers[session_id]

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.audio_buffers:
            self.audio_buffers[session_id].clear()
            del self.audio_buffers[session_id]
        if session_id in self.vad_segmenters:
            self.vad_segmenters[session_id].reset()
            del self.vad_segmenters[session_id]
        if session_id in self.turn_detectors:
            self.turn_detectors[session_id].reset()
            del self.turn_detectors[session_id]
        if session_id in self.whisper_services:
            del self.whisper_services[session_id]
        if session_id in self.kokoro_services:
            del self.kokoro_services[session_id]
        if session_id in self.orchestrators:
            del self.orchestrators[session_id]
        if session_id in self.examiner_speaking_states:
            del self.examiner_speaking_states[session_id]
        print(f"[WebSocketManager] Disconnected candidate session: {session_id}")

    def append_audio_chunk(self, session_id: str, chunk: bytes) -> Dict[str, Any]:
        """
        Appends incoming binary audio bytes into the session's AudioBuffer
        and processes the frame through the session's VADSegmenter.
        """
        if session_id not in self.audio_buffers:
            self.audio_buffers[session_id] = AudioBuffer(sample_rate=16000, channels=1, sample_width=2)
        if session_id not in self.vad_segmenters:
            self.vad_segmenters[session_id] = VADSegmenter()

        self.audio_buffers[session_id].append_chunk(chunk)
        vad_res = self.vad_segmenters[session_id].process_frame(chunk)
        return vad_res

    async def send_event(self, session_id: str, event: Dict[str, Any]):
        websocket = self.active_connections.get(session_id)
        if websocket:
            try:
                await websocket.send_text(json.dumps(event))
            except Exception as e:
                print(f"[WebSocketManager] Send event error for {session_id}: {e}")

    async def send_bytes(self, session_id: str, data: bytes):
        websocket = self.active_connections.get(session_id)
        if websocket:
            try:
                await websocket.send_bytes(data)
            except Exception as e:
                print(f"[WebSocketManager] Send bytes error for {session_id}: {e}")


# Global WebSocket Manager singleton
ws_manager = WebSocketManager()


async def emit_examiner_turn_with_tts(
    session_id: str,
    text: str,
    action: str,
    part: str,
    latency_metrics: Optional[Dict[str, float]] = None
):
    """
    Synthesizes examiner text response with Kokoro TTS,
    emits 'examiner_text', 'examiner_audio', 'examiner_response', and 'examiner.finished' events,
    and manages EXAMINER_SPEAKING state and mic feedback suppression.
    """
    ws_manager.set_examiner_speaking(session_id, True)
    await ws_manager.send_event(session_id, format_state_event(WebSocketState.EXAMINER_SPEAKING))
    
    # 1. Send examiner_text event
    await ws_manager.send_event(session_id, format_ws_event(WebSocketEventType.EXAMINER_TEXT.value, {
        "text": text,
        "action": action,
        "part": part
    }))

    kokoro = ws_manager.kokoro_services.get(session_id) or KokoroService()
    audio_res = kokoro.synthesize(text)
    
    # 2. Send examiner_audio WebSocket event
    audio_payload = {
        "text": text,
        "audio_base64": audio_res.audio_base64,
        "format": audio_res.format,
        "voice": audio_res.voice,
        "duration_sec": audio_res.duration_sec,
        "cached": audio_res.cached,
        "processing_time_sec": audio_res.processing_time_sec
    }
    if latency_metrics:
        audio_payload["latency_metrics"] = latency_metrics
    await ws_manager.send_event(session_id, format_ws_event(WebSocketEventType.EXAMINER_AUDIO.value, audio_payload))

    # 3. Send examiner_response text WebSocket event
    response_payload = {
        "text": text,
        "action": action,
        "part": part
    }
    if latency_metrics:
        response_payload["latency_metrics"] = latency_metrics
    await ws_manager.send_event(session_id, format_ws_event(WebSocketEventType.EXAMINER_RESPONSE.value, response_payload))

    # 4. Send examiner.finished event
    await ws_manager.send_event(session_id, format_ws_event(WebSocketEventType.EXAMINER_FINISHED.value, {
        "text": text,
        "part": part
    }))

    # 5. Return state to LISTENING and unblock candidate microphone input
    ws_manager.set_examiner_speaking(session_id, False)
    await ws_manager.send_event(session_id, format_ws_event(WebSocketEventType.LISTENING_STARTED.value, {
        "session_id": session_id,
        "part": part
    }))
    await ws_manager.send_event(session_id, format_state_event(WebSocketState.LISTENING))



async def handle_websocket_message(
    session_id: str,
    websocket: WebSocket,
    message: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Event router processing incoming WebSocket JSON control messages.
    Enforces server authority over examination state, safe exception handling, and protocol events.
    """
    try:
        msg_type = message.get("type")
        data = message.get("data", {})
        controller = ws_manager.controllers.get(session_id) or ExaminerController(session_id=session_id)
        qwen = ws_manager.qwen_services.get(session_id) or QwenService()

        # Reject client-driven unauthorized examination state mutation attempts
        if msg_type in ["set_part", "override_state", "force_part"]:
            return format_error_event(
                "Unauthorized examination state transition attempted by client. Server is sole authority.",
                code="UNAUTHORIZED_STATE_TRANSITION"
            )

        if msg_type == WebSocketEventType.PING.value:
            return format_ws_event(WebSocketEventType.PONG.value, {"timestamp": data.get("timestamp")})

        elif msg_type == "candidate_ready":
            await ws_manager.send_event(session_id, format_state_event(WebSocketState.LISTENING))
            return format_ws_event(WebSocketEventType.STATE.value, {
                "state": WebSocketState.LISTENING.value,
                "candidate_ready": True
            })

        elif msg_type == "stop_exam":
            await ws_manager.send_event(session_id, format_state_event(WebSocketState.COMPLETED))
            await ws_manager.send_event(session_id, format_ws_event(WebSocketEventType.SESSION_COMPLETE.value, {
                "message": "The examination was stopped by user request."
            }))
            return format_state_event(WebSocketState.COMPLETED)

        elif msg_type == WebSocketEventType.SESSION_START.value:
            q_info = controller.get_current_question_info()
            await ws_manager.send_event(session_id, format_state_event(WebSocketState.READY, {
                "part": controller.part.value,
                "state": controller.state.value,
                "question_id": q_info.get("id"),
                "topic": q_info.get("topic")
            }))
            
            # Send initial examiner prompt + Kokoro TTS audio
            first_q = q_info.get("question", "Where are you from?")
            await emit_examiner_turn_with_tts(session_id, first_q, ExaminerAction.ASK_NEXT.value, controller.part.value)
            return format_state_event(WebSocketState.LISTENING)

        elif msg_type == WebSocketEventType.SPEECH_START.value:
            await ws_manager.send_event(session_id, format_state_event(WebSocketState.LISTENING))
            return format_ws_event(WebSocketEventType.STATE.value, {"state": WebSocketState.LISTENING.value})

        elif msg_type == WebSocketEventType.AUDIO_START.value:
            buffer = ws_manager.audio_buffers.get(session_id)
            if buffer:
                buffer.clear()
            await ws_manager.send_event(session_id, format_state_event(WebSocketState.LISTENING))
            return format_ws_event(WebSocketEventType.STATE.value, {
                "state": WebSocketState.LISTENING.value,
                "sample_rate": data.get("sample_rate", 16000),
                "channels": data.get("channels", 1),
                "format": data.get("format", "pcm_s16le")
            })

        elif msg_type == WebSocketEventType.AUDIO_CHUNK.value:
            # Echo suppression guard: ignore incoming candidate mic audio while examiner is speaking
            if ws_manager.is_examiner_speaking(session_id):
                return format_ws_event(WebSocketEventType.STATE.value, {
                    "state": WebSocketState.EXAMINER_SPEAKING.value,
                    "echo_suppressed": True
                })

            buffer = ws_manager.audio_buffers.get(session_id)
            if not buffer:
                buffer = AudioBuffer(sample_rate=16000, channels=1, sample_width=2)
                ws_manager.audio_buffers[session_id] = buffer

            turn_detector = ws_manager.turn_detectors.get(session_id)
            if not turn_detector:
                turn_detector = TurnDetector(part_mode=controller.part.value)
                ws_manager.turn_detectors[session_id] = turn_detector
            else:
                turn_detector.set_part_mode(controller.part.value)

            chunk_bytes = b""
            if "samples" in data:
                buffer.append_float_array(data["samples"])
                import struct
                pcm_samples = [max(-32768, min(32767, int(s * 32768.0))) for s in data["samples"]]
                chunk_bytes = struct.pack(f"<{len(pcm_samples)}h", *pcm_samples)
            elif "raw_hex" in data:
                chunk_bytes = bytes.fromhex(data["raw_hex"])
                buffer.append_chunk(chunk_bytes)

            duration = buffer.get_duration_seconds()
            turn_res = {}
            if chunk_bytes:
                frame_ms = max(20, int((len(chunk_bytes) / 32000) * 1000))
                turn_res = turn_detector.process_frame(chunk_bytes, frame_duration_ms=frame_ms)

            event_type = turn_res.get("event_type")
            if event_type:
                ws_evt_map = {
                    "speech.started": WebSocketEventType.SPEECH_STARTED.value,
                    "speech.possible_end": WebSocketEventType.SPEECH_POSSIBLE_END.value,
                    "speech.resumed": WebSocketEventType.SPEECH_RESUMED.value,
                    "speech.ended": WebSocketEventType.SPEECH_ENDED.value
                }
                mapped_type = ws_evt_map.get(event_type, event_type)
                await ws_manager.send_event(session_id, format_ws_event(mapped_type, {
                    "state": turn_res.get("state"),
                    "event_type": event_type,
                    "part_mode": turn_res.get("part_mode"),
                    "silence_ms": turn_res.get("silence_ms"),
                    "speech_duration_ms": turn_res.get("speech_duration_ms"),
                    "total_duration_sec": turn_res.get("total_duration_sec"),
                    "end_reason": turn_res.get("end_reason")
                }))

            partial_text = ""
            # Generate and emit partial transcript for UI stream (if audio buffer >= 0.3s)
            if buffer and duration >= 0.3:
                wav_data = buffer.export_wav_bytes()
                whisper = ws_manager.whisper_services.get(session_id) or WhisperService()
                partial_obj = whisper.transcribe_partial(wav_data, language="en")
                partial_text = partial_obj.text

                # Emit transcript.partial ONLY to client UI (NEVER triggers Qwen)
                await ws_manager.send_event(session_id, format_ws_event(
                    WebSocketEventType.TRANSCRIPT_PARTIAL.value,
                    {
                        "text": partial_text,
                        "is_partial": True,
                        "language": partial_obj.language,
                        "processing_time_sec": partial_obj.processing_time_sec,
                        "rtf": partial_obj.rtf
                    }
                ))

            # Turn automatically finalized by turn detector endpointing
            if turn_res.get("is_finalized"):
                wav_data = buffer.export_wav_bytes()
                whisper = ws_manager.whisper_services.get(session_id) or WhisperService()
                
                tracker = PipelineLatencyTracker()
                tracker.start_stage("whisper")
                transcript_obj = whisper.transcribe_final(wav_data, language="en")
                asr_ms = tracker.end_stage("whisper")

                await ws_manager.send_event(session_id, format_ws_event(WebSocketEventType.TRANSCRIPT_FINAL.value, {
                    "text": transcript_obj.text,
                    "is_partial": False,
                    "language": transcript_obj.language,
                    "segments": [s.model_dump() for s in transcript_obj.segments],
                    "processing_time_sec": transcript_obj.processing_time_sec,
                    "rtf": transcript_obj.rtf
                }))

                # Transition to THINKING stage
                await ws_manager.send_event(session_id, format_state_event(WebSocketState.THINKING))
                await ws_manager.send_event(session_id, format_ws_event(WebSocketEventType.EXAMINER_THINKING.value, {
                    "status": "Generating examiner response...",
                    "candidate_text": transcript_obj.text
                }))

                tracker.start_stage("qwen")
                turn_result = controller.process_candidate_turn(
                    candidate_answer=transcript_obj.text,
                    qwen_service=qwen
                )
                qwen_ms = tracker.end_stage("qwen")

                tracker.start_stage("kokoro")
                await emit_examiner_turn_with_tts(
                    session_id,
                    turn_result["examiner_response"],
                    turn_result["action"],
                    turn_result["current_part"],
                    latency_metrics={"asr_ms": round(asr_ms, 2), "qwen_ms": round(qwen_ms, 2)}
                )
                tracker.end_stage("kokoro")
                turn_detector.reset()

            return format_ws_event(WebSocketEventType.STATE.value, {
                "state": WebSocketState.LISTENING.value,
                "buffered_duration_sec": round(duration, 3),
                "chunks_received": buffer.get_chunk_count() if buffer else 0,
                "partial_text": partial_text,
                "turn_state": turn_res.get("state", "LISTENING")
            })

        elif msg_type == WebSocketEventType.AUDIO_END.value:
            buffer = ws_manager.audio_buffers.get(session_id)
            whisper = ws_manager.whisper_services.get(session_id) or WhisperService()
            duration = buffer.get_duration_seconds() if buffer else 0.0
            sample_count = buffer.get_sample_count() if buffer else 0
            pcm_bytes = buffer.get_pcm_bytes() if buffer else b""
            total_bytes = len(pcm_bytes)
            
            await ws_manager.send_event(session_id, format_state_event(WebSocketState.PROCESSING, {
                "audio_duration_sec": round(duration, 3),
                "total_samples": sample_count,
                "total_bytes": total_bytes
            }))

            # Transcribe accumulated audio buffer via WhisperService transcribe_final
            transcript_obj = None
            turn_result = None

            if total_bytes > 0:
                wav_data = buffer.export_wav_bytes()
                tracker = PipelineLatencyTracker()
                tracker.start_stage("whisper")
                transcript_obj = whisper.transcribe_final(wav_data, language="en")
                asr_ms = tracker.end_stage("whisper")
                
                # 1. Send transcript.final event to client
                await ws_manager.send_event(session_id, format_ws_event(WebSocketEventType.TRANSCRIPT_FINAL.value, {
                    "text": transcript_obj.text,
                    "is_partial": False,
                    "language": transcript_obj.language,
                    "segments": [s.model_dump() for s in transcript_obj.segments],
                    "processing_time_sec": transcript_obj.processing_time_sec,
                    "rtf": transcript_obj.rtf
                }))

                # Legacy compatibility transcript event
                await ws_manager.send_event(session_id, format_ws_event(WebSocketEventType.TRANSCRIPT.value, {
                    "text": transcript_obj.text,
                    "language": transcript_obj.language
                }))

                # Transition state to THINKING
                await ws_manager.send_event(session_id, format_state_event(WebSocketState.THINKING))
                await ws_manager.send_event(session_id, format_ws_event(WebSocketEventType.EXAMINER_THINKING.value, {
                    "status": "Generating examiner response...",
                    "candidate_text": transcript_obj.text
                }))

                # 2. Authoritative final transcript feeds into ExaminerController & Qwen Service
                candidate_answer = transcript_obj.text
                tracker.start_stage("qwen")
                turn_result = controller.process_candidate_turn(
                    candidate_answer=candidate_answer,
                    qwen_service=qwen
                )
                qwen_ms = tracker.end_stage("qwen")

                tracker.start_stage("kokoro")
                await emit_examiner_turn_with_tts(
                    session_id,
                    turn_result["examiner_response"],
                    turn_result["action"],
                    turn_result["current_part"],
                    latency_metrics={"asr_ms": round(asr_ms, 2), "qwen_ms": round(qwen_ms, 2)}
                )
                tracker.end_stage("kokoro")

            return format_ws_event(WebSocketEventType.STATE.value, {
                "state": WebSocketState.EXAMINER_SPEAKING.value if turn_result else WebSocketState.PROCESSING.value,
                "audio_duration_sec": round(duration, 3),
                "total_bytes": total_bytes,
                "transcript": transcript_obj.text if transcript_obj else "",
                "final_transcript": transcript_obj.text if transcript_obj else ""
            })

        elif msg_type == WebSocketEventType.SPEECH_END.value:
            candidate_answer = data.get("transcript", "").strip()
            
            # Transition state to PROCESSING
            await ws_manager.send_event(session_id, format_state_event(WebSocketState.PROCESSING))

            if not candidate_answer:
                # Rephrase or prompt again
                current_q = controller.get_current_question_info().get("question", "Please answer the question.")
                await emit_examiner_turn_with_tts(
                    session_id,
                    f"I didn't quite catch that. {current_q}",
                    ExaminerAction.REPEAT.value,
                    controller.part.value
                )
                return format_state_event(WebSocketState.LISTENING)

            # Send transcript event back to client
            await ws_manager.send_event(session_id, format_ws_event(WebSocketEventType.TRANSCRIPT.value, {
                "text": candidate_answer
            }))

            # Transition state to THINKING
            await ws_manager.send_event(session_id, format_state_event(WebSocketState.THINKING))
            await ws_manager.send_event(session_id, format_ws_event(WebSocketEventType.EXAMINER_THINKING.value, {
                "status": "Generating examiner response...",
                "candidate_text": candidate_answer
            }))

            # Execute turn with Examiner Controller + Qwen Service
            tracker = PipelineLatencyTracker()
            tracker.start_stage("qwen")
            turn_result = controller.process_candidate_turn(
                candidate_answer=candidate_answer,
                qwen_service=qwen
            )
            qwen_ms = tracker.end_stage("qwen")

            await emit_examiner_turn_with_tts(
                session_id,
                turn_result["examiner_response"],
                turn_result["action"],
                turn_result["current_part"],
                latency_metrics={"qwen_ms": round(qwen_ms, 2)}
            )

            is_completed = turn_result.get("is_completed", False) or turn_result.get("state") == "completed"
            if is_completed:
                await ws_manager.send_event(session_id, format_ws_event(WebSocketEventType.SESSION_COMPLETE.value, {
                    "message": "The IELTS Speaking test is now complete."
                }))
                return format_state_event(WebSocketState.COMPLETED)

            # Transition back to LISTENING for next question
            return format_state_event(WebSocketState.LISTENING)

        else:
            return format_error_event(f"Unknown WebSocket event type: '{msg_type}'", code="UNKNOWN_EVENT")
    except Exception as err:
        print(f"[WebSocketManager] Internal handler exception for session {session_id}: {err}")
        return format_error_event("Speech processing error occurred. Please try again.", code="PIPELINE_ERROR")
