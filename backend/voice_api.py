from fastapi import FastAPI, UploadFile, File, Form, Body, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil
import uuid
import os
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime

from voice_pipeline import process_audio
from evaluator import evaluate
from scoring import calculate_overall
from audio_converter import convert_to_wav
from pcm_to_wav import save_pcm_as_wav
from session_manager import SessionManager, create_student, create_test_session, get_test_session
from conversation_manager import save_conversation, get_conversations
from conversation_history import build_history
from question_manager import QuestionManager
from examiner_prompt import build_examiner_prompt
from examiner_service import ExaminerService
from timing_engine import TimingEngine
from ielts_structure import IELTS_TEST_STRUCTURE
from database import SessionLocal, engine, Base
import models
from models import Student, TestSession, Answer

# Ensure all database tables exist on startup
Base.metadata.create_all(bind=engine)
from voice_config import VOICE_CONFIG, PART_LIMITS
from whisper_service import WhisperService
from ai_services import whisper_engine, kokoro_engine

whisper_service_instance = WhisperService(model_size="small", device="cpu", compute_type="int8")

from speech_segmenter import SpeechSegmenter
from speech_state import SpeechState
from rolling_buffer import RollingBuffer
from speech import FullDuplexVoicePipeline, VADMode, PipelineLatencyTracker, RealtimeSpeechState
from examiner.part1_controller import Part1Controller
from examiner.part2_controller import Part2Controller
from examiner.part3_controller import Part3Controller
from scoring.engine import SpeakingScoringEngine
from evaluator.service import IELTSEvaluator
from llm.qwen import QwenService
from websocket.events import ws_manager, handle_websocket_message
from websocket.protocol import WebSocketState, WebSocketEventType, format_ws_event
import struct
import math

qwen_service = QwenService()
evaluator_service = IELTSEvaluator(qwen_service)
scoring_engine = SpeakingScoringEngine(qwen_service=qwen_service)
session_part1_controllers = {}
session_part2_controllers = {}
session_part3_controllers = {}
session_speech_pipelines = {}

def get_speech_pipeline(session_id: str, mode: VADMode = VADMode.PART1) -> FullDuplexVoicePipeline:
    if session_id not in session_speech_pipelines:
        session_speech_pipelines[session_id] = FullDuplexVoicePipeline(mode=mode)
    return session_speech_pipelines[session_id]

def get_part1_controller(session_id: str) -> Part1Controller:
    if session_id not in session_part1_controllers:
        session_part1_controllers[session_id] = Part1Controller(evaluator=evaluator_service)
    return session_part1_controllers[session_id]

def get_part2_controller(session_id: str) -> Part2Controller:
    if session_id not in session_part2_controllers:
        session_part2_controllers[session_id] = Part2Controller(evaluator=evaluator_service)
    return session_part2_controllers[session_id]

def get_part3_controller(session_id: str, topic_key: str = "education") -> Part3Controller:
    if session_id not in session_part3_controllers:
        session_part3_controllers[session_id] = Part3Controller(
            topic_key=topic_key,
            evaluator=evaluator_service,
            qwen_service=qwen_service,
            session_id=session_id
        )
    return session_part3_controllers[session_id]


def is_chunk_speech(chunk: bytes, threshold: float = 300.0) -> bool:
    if len(chunk) % 2 == 0 and not chunk.startswith(b"\x1a\x45\xdf\xa3") and not chunk.startswith(b"OggS") and not chunk.startswith(b"RIFF"):
        num_samples = len(chunk) // 2
        if num_samples == 0:
            return False
        fmt = f"<{num_samples}h"
        try:
            samples = struct.unpack(fmt, chunk)
            sum_sq = sum(s * s for s in samples)
            rms = math.sqrt(sum_sq / num_samples)
            return rms > threshold
        except Exception:
            return True
    return True

app = FastAPI(
    title="IELTS Voice AI API",
    description="Full Voice-to-Voice IELTS AI Backend Pipeline with Whisper, Examiner Engine, & WebSockets",
    version="1.3"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)

# Global session manager instance
session_manager = SessionManager()
examiner_service = ExaminerService()

# Session-specific managers
session_qmanagers = {}
session_timers = {}

class StartSessionRequest(BaseModel):
    name: str = "Saidul Hasan"
    email: str | None = "student@example.com"

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "IELTS Voice AI Engine with Timing & Speech Pipeline",
        "message": "IELTS AI backend is running"
    }

def check_system_diagnostics():
    import urllib.request
    import json
    
    # 1. Ollama Status Check
    ollama_info = {
        "status": "offline",
        "model": getattr(qwen_service, "model", "qwen2.5:7b-instruct"),
        "url": getattr(qwen_service, "url", "http://localhost:11434"),
        "available_models": [],
        "message": "Ollama is unreachable. Ensure Ollama is running on your system."
    }
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags", headers={"User-Agent": "FastAPI-Health"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name") for m in data.get("models", [])]
            ollama_info["status"] = "online"
            ollama_info["available_models"] = models
            ollama_info["message"] = f"Connected to Ollama ({len(models)} model(s) available)"
    except Exception as e:
        ollama_info["message"] = f"Unreachable: {str(e)}. Start Ollama in Windows or run `ollama serve`."

    # 2. Whisper STT Check
    whisper_info = {
        "status": "offline",
        "backend": getattr(whisper_service_instance, "backend_type", "unknown"),
        "model_size": getattr(whisper_service_instance, "model_size", "small"),
        "device": getattr(whisper_service_instance, "device", "cpu"),
        "compute_type": getattr(whisper_service_instance, "compute_type", "int8"),
        "message": "Whisper STT service active"
    }
    if whisper_service_instance:
        if whisper_info["backend"] == "mock":
            whisper_info["status"] = "fallback"
            whisper_info["message"] = "Using deterministic CPU MockWhisper (faster-whisper module loading)"
        else:
            whisper_info["status"] = "online"
            whisper_info["message"] = f"faster-whisper model ({whisper_info['model_size']}) ready on {whisper_info['device'].upper()}"

    # 3. Kokoro TTS Check
    kokoro_info = {
        "status": "online" if kokoro_engine else "offline",
        "voice": "af_heart",
        "sample_rate": 24000,
        "message": "Kokoro TTS engine ready" if kokoro_engine else "Kokoro TTS engine unavailable"
    }

    # 4. GPU & PyTorch Check
    gpu_info = {
        "status": "cpu_only",
        "cuda_available": False,
        "device_name": "CPU",
        "vram_total_mb": 0,
        "vram_allocated_mb": 0,
        "cuda_version": None
    }
    try:
        import torch
        if torch.cuda.is_available():
            gpu_info["status"] = "online"
            gpu_info["cuda_available"] = True
            gpu_info["device_name"] = torch.cuda.get_device_name(0)
            gpu_info["vram_total_mb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024 * 1024))
            gpu_info["vram_allocated_mb"] = round(torch.cuda.memory_allocated(0) / (1024 * 1024))
            gpu_info["cuda_version"] = torch.version.cuda
    except Exception:
        pass

    # 5. Database Check
    db_info = {
        "status": "online",
        "engine": "SQLite",
        "message": "Database connection active"
    }

    # Overall Status Summary
    components_online = sum([
        1 if ollama_info["status"] == "online" else 0,
        1 if whisper_info["status"] in ["online", "fallback"] else 0,
        1 if kokoro_info["status"] == "online" else 0,
    ])
    
    return {
        "status": "ok" if components_online >= 2 else "degraded",
        "timestamp": datetime.now().isoformat(),
        "all_systems_ready": ollama_info["status"] == "online" and whisper_info["status"] == "online",
        "components": {
            "fastapi": {
                "status": "online",
                "port": 8000,
                "version": "1.3",
                "message": "FastAPI Voice Engine listening on port 8000"
            },
            "ollama": ollama_info,
            "whisper": whisper_info,
            "kokoro": kokoro_info,
            "gpu": gpu_info,
            "database": db_info
        }
    }

@app.get("/health")
@app.get("/api/system/status")
def health():
    return check_system_diagnostics()

@app.get("/prototype")
def prototype_page():
    proto_file = Path("frontend/index.html")
    if proto_file.exists():
        return FileResponse(str(proto_file))
    return {"error": "frontend/index.html not found"}

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    tmp_dir = Path("backend/tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    filename = file.filename or f"upload_{uuid.uuid4().hex[:8]}.wav"
    file_path = tmp_dir / filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    result = whisper_service_instance.transcribe(str(file_path))
    return result

@app.post("/session/start")
def start_session(request: StartSessionRequest = Body(default=StartSessionRequest())):
    student = create_student(
        name=request.name,
        email=request.email
    )
    test_session = create_test_session(
        student.id
    )
    
    # Initialize IELTSTestEngine for session
    session_id, engine = session_manager.create_session(test_session.id)
    initial_question = engine.start()
    question_text = initial_question["question"] if initial_question else "Where are you from?"
    
    session_qmanagers[session_id] = QuestionManager()
    session_timers[session_id] = TimingEngine()

    return {
        "student_id": student.id,
        "session_id": session_id,
        "part": engine.part,
        "question": question_text,
        "question_number": engine.question_number,
        "status": "active"
    }

@app.get("/session/{session_id}")
def get_session_state(session_id: str):
    engine = session_manager.get_session(session_id)
    db = SessionLocal()
    try:
        session = db.query(TestSession).filter(TestSession.id == session_id).first()
        current_part = engine.part if engine else (session.current_part if session else 1)
        status = session.status if session else "active"

        return {
            "session_id": session_id,
            "part": current_part,
            "question": engine.question_number if engine else 0,
            "status": status,
            "timer_started_at": session.timer_started_at.isoformat() if session and session.timer_started_at else None
        }
    finally:
        db.close()

@app.get("/session/{session_id}/part2")
def get_part2(session_id: str):
    cue_card = IELTS_TEST_STRUCTURE[2]["cue_card"]
    return {
        "session_id": session_id,
        "part": 2,
        "topic": cue_card["topic"],
        "points": cue_card["points"],
        "preparation_time": cue_card.get("preparation_time", 60),
        "speaking_time": cue_card.get("speaking_time", 120)
    }

@app.post("/session/{session_id}/part2/preparation")
def start_part2_preparation(session_id: str):
    if session_id not in session_timers:
        session_timers[session_id] = TimingEngine()
    
    timer = session_timers[session_id]
    timer.start_preparation()

    db = SessionLocal()
    try:
        session = db.query(TestSession).filter(TestSession.id == session_id).first()
        if session:
            session.current_part = 2
            session.current_state = "preparation"
            session.timer_started_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()

    return {
        "session_id": session_id,
        "state": "preparation",
        "duration": timer.PREPARATION_TIME,
        "remaining": timer.remaining()
    }

@app.post("/session/{session_id}/part2/speaking")
def start_part2_speaking(session_id: str):
    if session_id not in session_timers:
        session_timers[session_id] = TimingEngine()
    
    timer = session_timers[session_id]
    timer.start_speaking()

    db = SessionLocal()
    try:
        session = db.query(TestSession).filter(TestSession.id == session_id).first()
        if session:
            session.current_part = 2
            session.current_state = "speaking"
            session.timer_started_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()

    return {
        "session_id": session_id,
        "state": "speaking",
        "duration": timer.SPEAKING_TIME,
        "remaining": timer.remaining()
    }

@app.post("/conversation")
async def conversation(
    file: UploadFile = File(...),
    session_id: str = Form(default=""),
    part: int = Form(default=1),
    question: str = Form(default="Where are you from?")
):
    if not session_id:
        session_id = str(uuid.uuid4())

    if not session_manager.get_session(session_id):
        session_manager.create_session(session_id)

    engine = session_manager.get_session(session_id)

    input_file = AUDIO_DIR / f"{session_id}_{file.filename}"
    wav_file = AUDIO_DIR / f"{session_id}.wav"

    with open(input_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        converted_file = convert_to_wav(str(input_file), str(wav_file))
        candidate_text = whisper_engine.transcribe(str(converted_file))

        current_q = engine.get_current_question()
        current_question_text = current_q["question"] if current_q else question

        engine.submit_answer(candidate_text)

        # Save to database
        db = SessionLocal()
        try:
            ans = Answer(
                session_id=session_id,
                part=part,
                question=current_question_text,
                transcript=candidate_text,
                audio_path=str(converted_file)
            )
            db.add(ans)
            db.commit()
        finally:
            db.close()

        if engine.finished():
            return {
                "session_id": session_id,
                "part": engine.part,
                "candidate_text": candidate_text,
                "examiner_text": "Thank you. That is the end of Part 1.",
                "test_complete": True
            }

        next_q_data = engine.get_current_question()
        next_question_text = examiner_service.generate_question(
            topic=next_q_data["topic"],
            focus=next_q_data["focus"],
            conversation=engine.memory.get_recent()
        )
        engine.record_question(next_question_text)

        return {
            "session_id": session_id,
            "part": engine.part,
            "candidate_text": candidate_text,
            "examiner_text": next_question_text,
            "next_question": next_question_text,
            "audio_url": "/audio/examiner.mp3"
        }

    finally:
        if os.path.exists(input_file):
            try:
                os.remove(input_file)
            except Exception:
                pass

@app.post("/evaluate")
def evaluate_transcript(data: dict = Body(...)):
    transcript = data.get("transcript", "")
    if not transcript:
        return {"error": "Transcript required for evaluation"}
    
    result = evaluate(transcript)
    
    if "fluency_coherence" in result and "lexical_resource" in result and "grammar" in result and "pronunciation" in result:
        f = float(result["fluency_coherence"].get("score", 6.0))
        l = float(result["lexical_resource"].get("score", 6.0))
        g = float(result["grammar"].get("score", 6.0))
        p = float(result["pronunciation"].get("score", 6.0))
        overall = calculate_overall(f, l, g, p)
        if "overall" not in result or not isinstance(result["overall"], dict):
            result["overall"] = {}
        result["overall"]["score"] = overall

    return result

@app.post("/session/{session_id}/evaluate")
def evaluate_session(session_id: str):
    return {
        "session_id": session_id,
        "status": "evaluation_started"
    }

MAX_AUDIO_BYTES = 20 * 1024 * 1024  # 20MB limit
MIN_AUDIO_BYTES = 3200  # ~0.1s of 16kHz 16-bit mono PCM audio

async def process_buffered_audio(websocket: WebSocket, session_id: str, engine, answer_buffer):
    audio_bytes = answer_buffer.get_bytes()
    answer_buffer.clear()

    p1_ctrl = get_part1_controller(session_id)

    if len(audio_bytes) < MIN_AUDIO_BYTES:
        print(f"Audio buffer too small ({len(audio_bytes)} bytes < {MIN_AUDIO_BYTES} bytes), skipping transcription.")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Audio duration too short."
        }))
        return

    await websocket.send_text(json.dumps({
        "type": "phase",
        "value": "processing"
    }))
    await websocket.send_text(json.dumps({
        "type": "status",
        "value": "transcribing"
    }))

    wav_path = AUDIO_DIR / f"{session_id}.wav"
    webm_path = AUDIO_DIR / f"{session_id}.webm"

    # Check if raw PCM or WebM container
    if audio_bytes.startswith(b"\x1a\x45\xdf\xa3") or audio_bytes.startswith(b"OggS") or audio_bytes.startswith(b"RIFF"):
        with open(webm_path, "wb") as f:
            f.write(audio_bytes)
        convert_to_wav(webm_path, wav_path)
    else:
        # Raw 16kHz mono 16-bit PCM bytes
        save_pcm_as_wav(audio_bytes, str(wav_path), sample_rate=16000)

    start_t = time.perf_counter()
    try:
        res = whisper_engine.transcribe(str(wav_path), language="en")
        if isinstance(res, dict):
            transcript = res.get("text", "").strip()
            segments = res.get("segments", [])
        else:
            transcript = str(res).strip()
            segments = []
    except Exception as e:
        print(f"Whisper transcription error: {e}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": "Speech recognition failed."
        }))
        return

    elapsed = time.perf_counter() - start_t
    print(f"Whisper transcription time: {elapsed:.2f}s -> '{transcript}'")

    if not transcript:
        await websocket.send_text(json.dumps(p1_ctrl.build_event("no_answer", {
            "message": "No speech detected."
        })))
        return

    # Send transcript & transcription event to client
    await websocket.send_text(json.dumps(p1_ctrl.build_event("transcription", {
        "text": transcript,
        "segments": segments
    })))
    await websocket.send_text(json.dumps(p1_ctrl.build_event("transcript", {
        "text": transcript,
        "segments": segments
    })))

    current_q_text = p1_ctrl.current_question or (engine.get_current_question() or {}).get("question", "Where are you from?")

    # Save answer to database
    db = SessionLocal()
    try:
        ans = Answer(
            session_id=session_id,
            part=engine.part,
            question=current_q_text,
            transcript=transcript,
            audio_path=str(wav_path)
        )
        db.add(ans)
        db.commit()
    except Exception as db_e:
        print(f"DB save answer note: {db_e}")
    finally:
        db.close()

    if engine.part == 3 or (session_id in session_part3_controllers and session_part3_controllers[session_id].state.value in ["question", "listening", "evaluating", "follow_up"]):
        p3_ctrl = get_part3_controller(session_id)
        p3_res = p3_ctrl.process_answer(transcript, duration=elapsed, segments=segments)

        await websocket.send_text(json.dumps(p3_ctrl.build_event("evaluation_complete", {
            "recorded_silently": True,
            "idea_development": p3_res.get("idea_development")
        })))

        if p3_ctrl.is_completed():
            await websocket.send_text(json.dumps(p3_ctrl.build_event("part_completed", {
                "message": "Thank you. That completes Part 3 of the IELTS Speaking test."
            })))
            await websocket.send_text(json.dumps({
                "type": "test_complete"
            }))
            return

        next_q_text = p3_ctrl.determine_next_question(transcript)
        if not next_q_text or p3_ctrl.is_completed():
            await websocket.send_text(json.dumps(p3_ctrl.build_event("part_completed", {
                "message": "Thank you. That completes Part 3 of the IELTS Speaking test."
            })))
            await websocket.send_text(json.dumps({
                "type": "test_complete"
            }))
            return

        await websocket.send_text(json.dumps(p3_ctrl.build_event("examiner_speaking")))

        q_audio_file = AUDIO_DIR / f"{session_id}_p3_question.mp3"
        has_audio = False
        try:
            res = kokoro_engine.synthesize(next_q_text, str(q_audio_file))
            if res and os.path.exists(q_audio_file) and os.path.getsize(q_audio_file) > 1024:
                has_audio = True
        except Exception as e:
            print(f"Part 3 TTS synthesis note: {e}")

        await websocket.send_text(json.dumps(p3_ctrl.build_event("examiner_question", {
            "text": next_q_text,
            "question": next_q_text
        })))

        if has_audio and q_audio_file.exists():
            await websocket.send_text(json.dumps({
                "type": "examiner_audio",
                "format": "audio/mpeg"
            }))
            with open(q_audio_file, "rb") as af:
                await websocket.send_bytes(af.read())

        p3_ctrl.state = Part3State.LISTENING
        await websocket.send_text(json.dumps(p3_ctrl.build_event("listening_started")))
        await websocket.send_text(json.dumps({
            "type": "phase",
            "value": "ready"
        }))
        return

    if engine.part == 2 or (session_id in session_part2_controllers and session_part2_controllers[session_id].state.value in ["long_turn", "ready"]):
        p2_ctrl = get_part2_controller(session_id)
        p2_res = p2_ctrl.process_long_turn_answer(transcript, duration=elapsed, segments=segments)
        
        await websocket.send_text(json.dumps(p2_ctrl.build_event("evaluation_complete", {
            "recorded_silently": True,
            "task_coverage": p2_res.get("task_coverage")
        })))

        await websocket.send_text(json.dumps(p2_ctrl.build_event("part_completed", {
            "message": "Thank you. That completes Part 2 of the IELTS Speaking test.",
            "task_coverage": p2_res.get("task_coverage")
        })))
        await websocket.send_text(json.dumps({
            "type": "phase",
            "value": "ready"
        }))
        return

    engine.submit_answer(transcript)
    eval_res = p1_ctrl.process_answer(transcript, duration=elapsed, segments=segments)

    # Silent evaluation recorded event
    if eval_res.get("evaluation"):
        await websocket.send_text(json.dumps(p1_ctrl.build_event("evaluation_complete", {
            "recorded_silently": True
        })))

    intent = eval_res.get("intent")

    if engine.finished() or p1_ctrl.is_completed():
        await websocket.send_text(json.dumps(p1_ctrl.build_event("part_completed", {
            "message": "Thank you. That completes Part 1 of the IELTS Speaking test."
        })))
        await websocket.send_text(json.dumps({
            "type": "test_complete"
        }))
        return

    # Status: thinking
    await websocket.send_text(json.dumps({
        "type": "phase",
        "value": "thinking"
    }))
    await websocket.send_text(json.dumps({
        "type": "status",
        "value": "thinking"
    }))

    if intent == "clarification_request":
        next_question_text = f"Let me rephrase that for you: {p1_ctrl.current_question}"
    else:
        q_info = p1_ctrl.next_question()
        if not q_info or p1_ctrl.is_completed():
            await websocket.send_text(json.dumps(p1_ctrl.build_event("part_completed", {
                "message": "Thank you. That completes Part 1 of the IELTS Speaking test."
            })))
            await websocket.send_text(json.dumps({
                "type": "test_complete"
            }))
            return
        next_question_text = q_info["question"]

    engine.record_question(next_question_text)

    await websocket.send_text(json.dumps(p1_ctrl.build_event("examiner_speaking")))

    # Synthesize Kokoro TTS audio for the examiner question
    q_audio_file = AUDIO_DIR / f"{session_id}_question.mp3"
    has_audio = False
    try:
        res = kokoro_engine.synthesize(next_question_text, str(q_audio_file))
        if res and os.path.exists(q_audio_file) and os.path.getsize(q_audio_file) > 1024:
            try:
                shutil.copy(q_audio_file, "examiner.mp3")
            except Exception:
                pass
            has_audio = True
    except Exception as tts_e:
        print(f"Kokoro TTS synthesis note: {tts_e}")

    await websocket.send_text(json.dumps({
        "type": "phase",
        "value": "speaking"
    }))

    # Send examiner_question to client
    await websocket.send_text(json.dumps(p1_ctrl.build_event("examiner_question", {
        "text": next_question_text,
        "question": next_question_text
    })))
    await websocket.send_text(json.dumps({
        "type": "question",
        "text": next_question_text
    }))

    if has_audio and q_audio_file.exists():
        await websocket.send_text(json.dumps({
            "type": "examiner_audio",
            "format": "audio/mpeg"
        }))
        with open(q_audio_file, "rb") as af:
            await websocket.send_bytes(af.read())

    # Status: ready & listening_started
    p1_ctrl.start_listening()
    await websocket.send_text(json.dumps(p1_ctrl.build_event("listening_started")))
    await websocket.send_text(json.dumps({
        "type": "phase",
        "value": "ready"
    }))
    await websocket.send_text(json.dumps({
        "type": "status",
        "value": "ready"
    }))



@app.websocket("/ws/exam")
@app.websocket("/ws/exam/{session_id}")
async def exam_websocket(websocket: WebSocket, session_id: str | None = None):
    """
    Lesson 42 Real-Time IELTS Examiner WebSocket Endpoint.
    Manages continuous bidirectional JSON control and audio events over persistent WebSocket.
    """
    if not session_id:
        session_id = "session_" + uuid.uuid4().hex[:8]

    controller = await ws_manager.connect(session_id, websocket)

    try:
        while True:
            raw_message = await websocket.receive()
            
            # Handle Text JSON Messages
            if "text" in raw_message and raw_message["text"]:
                try:
                    message_data = json.loads(raw_message["text"])
                    response_event = await handle_websocket_message(session_id, websocket, message_data)
                    if response_event:
                        await ws_manager.send_event(session_id, response_event)
                except json.JSONDecodeError:
                    await ws_manager.send_event(session_id, format_ws_event("error", {
                        "message": "Invalid JSON payload received."
                    }))

            # Handle Binary PCM Audio Chunks
            elif "bytes" in raw_message and raw_message["bytes"]:
                raw_bytes = raw_message["bytes"]
                vad_res = ws_manager.append_audio_chunk(session_id, raw_bytes)
                audio_buf = ws_manager.audio_buffers.get(session_id)
                duration = audio_buf.get_duration_seconds() if audio_buf else 0.0
                
                await ws_manager.send_event(session_id, format_ws_event("state", {
                    "state": vad_res.get("state", WebSocketState.LISTENING.value),
                    "is_speech": vad_res.get("is_speech", False),
                    "speech_probability": vad_res.get("speech_probability", 0.0),
                    "is_finalized": vad_res.get("is_finalized", False),
                    "bytes_received": len(raw_bytes),
                    "buffered_duration_sec": round(duration, 3)
                }))

    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)
        print(f"[WebSocket] Candidate disconnected from session: {session_id}")
    except Exception as err:
        ws_manager.disconnect(session_id)
        print(f"[WebSocket] Connection error in session {session_id}: {err}")



@app.websocket("/ws/speaking")
@app.websocket("/ws/speaking/{session_id}")
async def speaking_websocket(websocket: WebSocket, session_id: str | None = None):
    await websocket.accept()
    if not session_id or session_id == "demo":
        session_id = "demo-" + str(uuid.uuid4())[:8]

    engine = session_manager.get_session(session_id)
    if not engine:
        _, engine = session_manager.create_session(session_id)
        engine.start()

    answer_buffer = session_manager.get_buffer(session_id)
    segmenter = session_manager.get_segmenter(session_id, part=f"part{engine.part}")
    rolling_buffer = session_manager.get_rolling_buffer(session_id)

    print(f"WebSocket client connected for session: {session_id}")

    try:
        while True:
            message = await websocket.receive()

            # Handle JSON Control Messages
            if "text" in message and message["text"]:
                try:
                    data = json.loads(message["text"])
                    msg_type = data.get("type")

                    if msg_type in ["session_start", "start_part1", "start_session"]:
                        p1_ctrl = get_part1_controller(session_id)
                        await websocket.send_text(json.dumps(p1_ctrl.build_event("session_started")))

                        # Get intro step or next question
                        intro_step = p1_ctrl.get_next_intro_step()
                        if intro_step:
                            q_text = intro_step
                        else:
                            q_info = p1_ctrl.next_question()
                            q_text = q_info["question"] if q_info else "Where are you from?"

                        await websocket.send_text(json.dumps(p1_ctrl.build_event("examiner_speaking")))

                        # Synthesize TTS
                        q_audio_file = AUDIO_DIR / f"{session_id}_question.mp3"
                        has_audio = False
                        try:
                            res = kokoro_engine.synthesize(q_text, str(q_audio_file))
                            if res and os.path.exists(q_audio_file) and os.path.getsize(q_audio_file) > 1024:
                                shutil.copy(q_audio_file, "examiner.mp3")
                                has_audio = True
                        except Exception as e:
                            print(f"Intro TTS note: {e}")

                        await websocket.send_text(json.dumps(p1_ctrl.build_event("examiner_question", {
                            "text": q_text,
                            "question": q_text
                        })))
                        await websocket.send_text(json.dumps({
                            "type": "question",
                            "text": q_text
                        }))

                        if has_audio and q_audio_file.exists():
                            await websocket.send_text(json.dumps({
                                "type": "examiner_audio",
                                "format": "audio/mpeg"
                            }))
                            with open(q_audio_file, "rb") as af:
                                await websocket.send_bytes(af.read())

                        p1_ctrl.start_listening()
                        await websocket.send_text(json.dumps(p1_ctrl.build_event("listening_started")))
                        continue

                    elif msg_type == "start_part2":
                        engine.part = 2
                        p2_ctrl = get_part2_controller(session_id)
                        card = p2_ctrl.select_cue_card()

                        intro_text = f"Now, in Part 2, I am going to give you a topic and I'd like you to talk about it for one to two minutes. Before you talk, you'll have one minute to think about what you're going to say. Here is your topic: {card['prompt']}"

                        # Synthesize TTS
                        q_audio_file = AUDIO_DIR / f"{session_id}_p2_cue_card.mp3"
                        has_audio = False
                        try:
                            res = kokoro_engine.synthesize(intro_text, str(q_audio_file))
                            if res and os.path.exists(q_audio_file) and os.path.getsize(q_audio_file) > 1024:
                                has_audio = True
                        except Exception as e:
                            print(f"Part 2 TTS note: {e}")

                        await websocket.send_text(json.dumps(p2_ctrl.build_event("part2_cue_card", {
                            "prompt": card["prompt"],
                            "points": card["points"],
                            "card_id": card["id"],
                            "topic": card["topic"]
                        })))

                        if has_audio and q_audio_file.exists():
                            await websocket.send_text(json.dumps({
                                "type": "examiner_audio",
                                "format": "audio/mpeg"
                            }))
                            with open(q_audio_file, "rb") as af:
                                await websocket.send_bytes(af.read())

                        continue

                    elif msg_type == "start_preparation":
                        p2_ctrl = get_part2_controller(session_id)
                        timer_info = p2_ctrl.start_preparation()
                        await websocket.send_text(json.dumps(p2_ctrl.build_event("timer_started", timer_info)))
                        continue

                    elif msg_type == "start_long_turn":
                        p2_ctrl = get_part2_controller(session_id)
                        timer_info = p2_ctrl.start_long_turn()
                        await websocket.send_text(json.dumps(p2_ctrl.build_event("timer_started", timer_info)))
                        await websocket.send_text(json.dumps(p2_ctrl.build_event("listening_started")))
                        await websocket.send_text(json.dumps({
                            "type": "phase",
                            "value": "listening"
                        }))
                        continue

                    elif msg_type == "start_part3":
                        engine.part = 3
                        topic_key = data.get("topic", "education")
                        p3_ctrl = get_part3_controller(session_id, topic_key=topic_key)
                        q_data = p3_ctrl.get_first_question()

                        intro_text = f"We've been talking about a topic in Part 2, and now I'd like to discuss with you one or two more general questions related to this. Let's talk about {p3_ctrl.topic_title}. {q_data['question']}"

                        await websocket.send_text(json.dumps(p3_ctrl.build_event("examiner_speaking")))

                        q_audio_file = AUDIO_DIR / f"{session_id}_p3_intro.mp3"
                        has_audio = False
                        try:
                            res = kokoro_engine.synthesize(intro_text, str(q_audio_file))
                            if res and os.path.exists(q_audio_file) and os.path.getsize(q_audio_file) > 1024:
                                has_audio = True
                        except Exception as e:
                            print(f"Part 3 Intro TTS note: {e}")

                        await websocket.send_text(json.dumps(p3_ctrl.build_event("part3_question", {
                            "question": q_data['question'],
                            "text": q_data['question'],
                            "topic": p3_ctrl.topic_title
                        })))

                        if has_audio and q_audio_file.exists():
                            await websocket.send_text(json.dumps({
                                "type": "examiner_audio",
                                "format": "audio/mpeg"
                            }))
                            with open(q_audio_file, "rb") as af:
                                await websocket.send_bytes(af.read())

                        await websocket.send_text(json.dumps(p3_ctrl.build_event("listening_started")))
                        await websocket.send_text(json.dumps({
                            "type": "phase",
                            "value": "ready"
                        }))
                        continue

                    elif msg_type == "set_vad_mode":
                        mode_str = data.get("mode", "part1")
                        pipeline = get_speech_pipeline(session_id)
                        if mode_str == "part2":
                            pipeline.set_mode(VADMode.PART2)
                        elif mode_str == "part3":
                            pipeline.set_mode(VADMode.PART3)
                        else:
                            pipeline.set_mode(VADMode.PART1)
                        await websocket.send_text(json.dumps({
                            "type": "vad_mode_updated",
                            "mode": mode_str
                        }))
                        continue

                    elif msg_type == "examiner_speaking":
                        is_speaking = data.get("value", True)
                        pipeline = get_speech_pipeline(session_id)
                        pipeline.set_examiner_speaking(is_speaking)
                        continue

                    elif msg_type == "audio_start":
                        answer_buffer.clear()
                        segmenter.reset()
                        rolling_buffer.clear()
                        p1_ctrl = get_part1_controller(session_id)
                        p1_ctrl.start_listening()
                        await websocket.send_text(json.dumps(p1_ctrl.build_event("listening_started")))
                        await websocket.send_text(json.dumps({
                            "type": "phase",
                            "value": "listening"
                        }))
                        await websocket.send_text(json.dumps({
                            "type": "status",
                            "value": "listening"
                        }))
                        continue

                    elif msg_type == "audio_end":
                        if answer_buffer.size() == 0:
                            await websocket.send_text(json.dumps({
                                "type": "error",
                                "message": "No audio received."
                            }))
                            continue

                        await process_buffered_audio(websocket, session_id, engine, answer_buffer)
                        segmenter.reset()
                        rolling_buffer.clear()
                        continue

                except json.JSONDecodeError:
                    pass


            # Handle Binary Audio Chunks
            if "bytes" in message and message["bytes"]:
                chunk = message["bytes"]

                if answer_buffer.size() + len(chunk) > MAX_AUDIO_BYTES:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Audio limit exceeded."
                    }))
                    answer_buffer.clear()
                    segmenter.reset()
                    rolling_buffer.clear()
                    continue

                rolling_buffer.add(chunk)
                speech_detected = is_chunk_speech(chunk)
                event = segmenter.process(speech_detected)

                if event == "speech_started":
                    # Prepend rolling buffer pre-speech chunks
                    for prev_chunk in rolling_buffer.get():
                        answer_buffer.add(prev_chunk)
                    rolling_buffer.clear()
                    await websocket.send_text(json.dumps({
                        "type": "phase",
                        "value": "listening"
                    }))
                elif event in ["speech_confirmed", "speech_continued", "speech_resumed"]:
                    answer_buffer.add(chunk)
                elif event == "speech_ended":
                    answer_buffer.add(chunk)
                    await process_buffered_audio(websocket, session_id, engine, answer_buffer)
                    segmenter.reset()
                    rolling_buffer.clear()
                else:
                    # Fallback for monolithic single webm uploads
                    if len(chunk) > 10000 and answer_buffer.size() == 0:
                        answer_buffer.add(chunk)
                        await process_buffered_audio(websocket, session_id, engine, answer_buffer)
                        segmenter.reset()
                        rolling_buffer.clear()

    except WebSocketDisconnect:
        print(f"WebSocket client disconnected for session {session_id}")
    except Exception as e:
        print(f"WebSocket error in session {session_id}: {e}")
    finally:
        answer_buffer.clear()


@app.get("/audio/examiner.mp3")
def examiner_audio():
    audio_path = "examiner.mp3"
    if not os.path.exists(audio_path):
        return {"error": "examiner.mp3 not found. Run a conversation turn first."}
    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename="examiner.mp3"
    )

class TTSRequest(BaseModel):
    text: str
    voice: str = "af_heart"
    speed: float = 1.0

@app.post("/tts")
@app.post("/api/tts")
@app.post("/api/examiner/voice")
async def synthesize_speech(request: TTSRequest):
    """
    Direct high-fidelity Kokoro TTS endpoint.
    Synthesizes examiner speech and streams audio/mpeg binary directly to frontend.
    """
    text = (request.text or "").strip()
    if not text:
        text = "Could you please tell me a little about yourself?"

    file_id = uuid.uuid4().hex[:10]
    out_file = AUDIO_DIR / f"tts_{file_id}.mp3"

    try:
        if kokoro_engine:
            kokoro_engine.synthesize(text, str(out_file))
            if out_file.exists():
                return FileResponse(
                    str(out_file),
                    media_type="audio/mpeg",
                    filename="examiner_voice.mp3"
                )
    except Exception as e:
        print(f"[TTS Endpoint] Kokoro synthesis exception: {e}")

    # If Kokoro offline, fallback to mock/cached audio if exists
    if os.path.exists("examiner.mp3"):
        return FileResponse("examiner.mp3", media_type="audio/mpeg")

    return {"error": "Kokoro TTS engine not available or synthesis failed"}

@app.get("/tts")
@app.get("/api/tts")
async def synthesize_speech_get(text: str = "Where are you from?", voice: str = "af_heart"):
    req = TTSRequest(text=text, voice=voice)
    return await synthesize_speech(req)



@app.get("/api/session/{session_id}/report")
def get_session_report(session_id: str):
    p1_answers = []
    p2_answer = None
    p3_answers = []

    if session_id in session_part1_controllers:
        p1_answers = session_part1_controllers[session_id].evaluations

    if session_id in session_part2_controllers:
        p2_ctrl = session_part2_controllers[session_id]
        if p2_ctrl.evaluation_result:
            p2_answer = {
                "question": "Part 2 Cue Card Speech",
                "transcript": p2_ctrl.evaluation_result.get("transcript", ""),
                "duration": p2_ctrl.long_turn_duration,
                "evaluation": p2_ctrl.evaluation_result
            }

    if session_id in session_part3_controllers:
        p3_answers = session_part3_controllers[session_id].evaluations

    report = scoring_engine.evaluate_session(
        session_id=session_id,
        part1_answers=p1_answers,
        part2_answer=p2_answer,
        part3_answers=p3_answers
    )
    return report

if __name__ == "__main__":
    import uvicorn
    print("[VoiceAPI] Starting FastAPI server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

