import React, { useState } from 'react';
import { HARDWARE_PRESETS } from '../data/topics';
import { Server, Cpu, Terminal, Layers, Code, CheckCircle2, Copy, Check, Play, BookOpen, ShieldCheck, Zap, Download, Radio, Database, FileText } from 'lucide-react';

export const LocalDeploymentGuide: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'a-to-z' | 'architecture' | 'stages' | 'code' | 'hardware'>('a-to-z');
  const [selectedVram, setSelectedVram] = useState<number>(12);
  const [copiedIndex, setCopiedIndex] = useState<string | null>(null);

  const handleCopy = (code: string, id: string) => {
    navigator.clipboard.writeText(code);
    setCopiedIndex(id);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const aToZSteps = [
    {
      step: 'Lesson 1',
      title: 'Environment & Prerequisites Setup',
      desc: 'Install Python 3.10+, Node.js 18+, FFmpeg, and Git on your local machine.',
      code: `# Linux / macOS setup
sudo apt update && sudo apt install -y python3-venv ffmpeg git nodejs npm

# Verify installations
python3 --version
ffmpeg -version
node -v`
    },
    {
      step: 'Lesson 2',
      title: 'Local LLM Setup with Ollama & Qwen 3',
      desc: 'Download and start Ollama to run the Qwen 3 (8B) model locally for examiner reasoning.',
      code: `# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull and start Qwen 3 (8B)
ollama pull qwen3:8b
ollama run qwen3:8b`
    },
    {
      step: 'Lesson 3',
      title: 'Speech-to-Text with faster-whisper',
      desc: 'Set up Python virtual environment and install faster-whisper for local microphone STT.',
      code: `mkdir -p ~/ielts-ai/backend && cd ~/ielts-ai/backend
python3 -m venv venv
source venv/bin/activate
pip install faster-whisper fastapi "uvicorn[standard]" websockets python-multipart requests sqlalchemy pydantic`
    },
    {
      step: 'Lesson 4',
      title: 'Text-to-Speech Voice Engine (Kokoro TTS)',
      desc: 'Run the Kokoro TTS container on port 8880 for studio-quality examiner audio synthesis.',
      code: `# Run Kokoro Docker container
docker run -d -p 8880:8880 --gpus all ghcr.io/kokoro-tts/kokoro-fastapi:latest

# Test TTS endpoint
curl -X POST http://localhost:8880/v1/audio/speech \\
  -H "Content-Type: application/json" \\
  -d '{"model":"kokoro","input":"Good morning","voice":"af_heart"}' --output test.mp3`
    },
    {
      step: 'Lesson 5',
      title: 'FFmpeg Audio Normalization',
      desc: 'Convert WebM/Opus browser mic recordings into 16 kHz mono WAV for Whisper processing.',
      code: `# audio_converter.py
import subprocess, os

def convert_to_wav(input_file, output_file):
    command = ["ffmpeg", "-y", "-i", input_file, "-ar", "16000", "-ac", "1", output_file]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_file`
    },
    {
      step: 'Lesson 6',
      title: 'Ollama + Whisper + Kokoro Integrated Voice Pipeline',
      desc: 'Combine STT, LLM examiner reasoning, and TTS into a unified backend function.',
      code: `# Test complete pipeline locally
python voice_pipeline.py`
    },
    {
      step: 'Lesson 7',
      title: 'IELTS Band Scoring Engine & Evaluation',
      desc: 'Post-test transcript evaluation across 4 criteria: FC, LR, GRA, and PR.',
      code: `# Run evaluation on sample transcript
python evaluator.py`
    },
    {
      step: 'Lesson 8',
      title: 'SQLite Database & Session Management',
      desc: 'Set up SQLAlchemy models for Student, TestSession, Conversation, and Evaluation.',
      code: `# Initialize SQLite DB ielts.db
python create_database.py`
    },
    {
      step: 'Lesson 9',
      title: 'FastAPI Voice API Server',
      desc: 'Launch FastAPI server on port 8000 handling audio upload and evaluation.',
      code: `# Start backend server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
    },
    {
      step: 'Lesson 10',
      title: 'Real-Time IELTS Conversation Frontend',
      desc: 'Start React frontend on port 5173 connected to session management and real-time mic controls.',
      code: `# Start React frontend
cd ~/ielts-ai/frontend
npm run dev`
    },
    {
      step: 'Lesson 11',
      title: 'Build the IELTS Examiner Engine',
      desc: 'Structured question bank, state machine (Part 1/2/3), Part 2 timers, and examiner mode prompts.',
      code: `# Test examiner engine and question manager
python test_examiner_engine.py
python test_question_manager.py`
    },
    {
      step: 'Lesson 12',
      title: 'IELTS Timing Engine & Part 2 Control',
      desc: 'Timing engine with 60s preparation and 120s speaking timers, DB state tracking, and session recovery.',
      code: `# Test timing engine locally
python test_timing.py`
    },
    {
      step: 'Lesson 13',
      title: 'Advanced Qwen Examiner & Conversation Memory',
      desc: 'Conversation memory, candidate context facts, anti-repetition validator, and Part 3 progression strategies.',
      code: `# Test memory module locally
python test_memory.py`
    },
    {
      step: 'Lesson 14',
      title: 'Automatic IELTS Speaking Evaluation Engine',
      desc: 'Post-test evaluator prompt, structured JSON score format, speech WPM metrics, and separate candidate answer database storage.',
      code: `# Test evaluation score and metrics
python test_score.py
python test_metrics.py`
    },
    {
      step: 'Lesson 15',
      title: 'Pronunciation + Audio Intelligence',
      desc: 'Multi-signal Librosa audio analyzer detecting pause statistics, speech percentage, pitch YIN analysis, pitch variation, and audio metrics for Qwen.',
      code: `# Install audio analysis foundation
pip install librosa soundfile numpy

# Test librosa audio analyzer module
python -c "import librosa; print('Librosa version:', librosa.__version__)"`
    },
    {
      step: 'Lesson 16',
      title: 'Real-Time Voice Conversation & VAD Engine',
      desc: 'Silero VAD speech detection, automatic silence stop, voice configuration limits, and WebSocket /ws/speaking connection.',
      code: `# Install Silero VAD, PyTorch, torchaudio
pip install torch torchaudio silero-vad

# Test VAD Engine locally
python test_vad.py`
    },
    {
      step: 'Lesson 17',
      title: 'Build Complete End-to-End MVP',
      desc: 'Unified end-to-end architecture connecting deterministic IELTS Engine, Qwen Examiner service, Config, and SQLite database.',
      code: `# Verify backend requirements and configuration
pip install -r requirements.txt
cat config.py && cat .env

# Initialize database schema
python create_database.py

# Test Qwen integration and deterministic test engine
python test_qwen.py
python test_engine.py`
    },
    {
      step: 'Lesson 18',
      title: 'React Frontend + Browser Microphone & WebSocket',
      desc: 'Connect browser getUserMedia microphone, MediaRecorder, Blob audio transmission, and WebSocket connection to FastAPI.',
      code: `# Run React frontend dev server
cd ~/ielts-ai/frontend
npm run dev

# Run FastAPI backend with WebSockets
cd ~/ielts-ai/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
    },
    {
      step: 'Lesson 19',
      title: 'Integrate Whisper Speech-to-Text',
      desc: 'Singleton Whisper instance, FFmpeg audio conversion to 16kHz mono WAV, real-time transcription, and WebSocket JSON status messages.',
      code: `# Test standalone Whisper speech-to-text
python test_whisper.py`
    },
    {
      step: 'Lesson 20',
      title: 'Connect Whisper → IELTS Engine → Qwen Examiner',
      desc: 'Complete multi-turn conversational IELTS loop with deterministic test engine, Qwen phrasing generator, conversation memory, and session management.',
      code: `# Test Qwen examiner service
python test_examiner.py

# Test engine with conversation memory
python test_engine.py`
    },
    {
      step: 'Lesson 21',
      title: 'Integrate Kokoro TTS: Make AI Examiner Speak',
      desc: 'KokoroEngine speech synthesis, ai_services singleton container, WebSocket MP3 ArrayBuffer streaming, and React audio playback with microphone recording guards.',
      code: `# Test Kokoro TTS endpoint & KokoroEngine
python test_kokoro.py
python test_kokoro_engine.py

# Launch FastAPI backend with full Voice-to-Voice AI pipeline
uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
    },
    {
      step: 'Lesson 22',
      title: 'Automatic Voice Activity Detection (VAD)',
      desc: 'Web Audio API RMS Voice Activity Detector hook (useVAD.ts), automatic silence detection (1.5s), 60s safety answer cap, VAD SPEECH/SILENCE badge, and real-time audio level visualizer.',
      code: `# Launch React frontend with automatic VAD silence stopping
cd ~/ielts-ai/frontend
npm run dev`
    },
    {
      step: 'Lesson 23',
      title: 'Production-Quality VAD with Silero VAD',
      desc: 'Silero VAD deep learning model integration (VADEngine in vad_engine.py), SpeechSegment audio buffer & padding manager (speech_segment.py), test_vad.py, and centralized Settings class in config.py.',
      code: `# Install Silero VAD & PyTorch dependencies
pip install torch torchaudio silero-vad

# Test Silero VAD speech timestamp detection
python test_vad.py`
    },
    {
      step: 'Lesson 24',
      title: 'Real-Time WebSocket Audio Streaming',
      desc: 'Continuous 100ms MediaRecorder audio chunk streaming, audio_start / audio_end binary protocol, session-specific AnswerBuffer (answer_buffer.py) with 20MB guard limit, and server phase control broadcasts.',
      code: `# Test AnswerBuffer functionality
python test_buffer.py

# Launch FastAPI backend with real-time WebSocket audio streaming
uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
    },
    {
      step: 'Lesson 25',
      title: 'Browser Microphone → 16 kHz PCM Streaming',
      desc: 'Web Audio API PCMStreamer (src/audio/PCMStreamer.ts) & linear interpolation resampler (src/audio/resample.ts) converting microphone Float32 audio into 16,000 Hz mono 16-bit PCM binary ArrayBuffers. Direct PCM-to-WAV helper (pcm_to_wav.py) without FFmpeg decoding.'
    },
    {
      step: 'Lesson 26',
      title: 'Real-Time Speech Segmentation & Endpoint Detection',
      desc: '5-state SpeechSegmenter machine (speech_segmenter.py & speech_state.py) with 250ms RollingBuffer (rolling_buffer.py) pre-speech audio boundaries. Part-specific PART_CONFIG timing rules and real-time RMS chunk speech detection.'
    },
    {
      step: 'Lesson 27',
      title: 'Connect Speech Segmentation to Whisper STT',
      desc: 'Connect finalized speech segmentation buffers directly to faster-whisper STT engine via WhisperService (whisper_service.py). Supports language="en" forcing for IELTS and returns transcript with segment timestamps (start, end, text). Empty audio/short buffer protection (3200 bytes) and audio_utils.py PCM-to-WAV conversion.'
    },
    {
      step: 'Lesson 28',
      title: 'Build the IELTS Speaking Examiner Brain',
      desc: 'Separate application control from LLM text generation. Created IELTSSession (examiner/session.py) for session state and answer logs, QuestionManager (examiner/manager.py) and controlled question bank (examiner/questions.py), QwenService (llm/qwen.py), and SYSTEM_PROMPT (examiner/prompts.py) ensuring strict examiner behavior.'
    },
    {
      step: 'Lesson 29',
      title: 'Build the IELTS Evaluation Engine with Qwen',
      desc: 'Built structured evaluation dataclasses (evaluator/models.py), speech metrics features (evaluator/speech_features.py), prompt insulation with <CANDIDATE_ANSWER> markers (evaluator/prompts.py), deterministic band scoring (evaluator/scoring.py), and IELTSEvaluator service (evaluator/service.py) with Qwen LLM criteria analysis.'
    },
    {
      step: 'Lesson 30',
      title: 'Build the Complete IELTS Speaking Part 1 Engine',
      desc: 'Created complete Part 1 state machine (Part1State), PART_1_CONFIG with introduction sequence, Part1Controller with candidate response intent classification (clarification vs valid answer vs no answer), silent server-side Qwen evaluation, and standardized WebSocket event protocol (session_started, examiner_speaking, listening_started, transcript, evaluation_complete, examiner_question, part_completed).'
    },
    {
      step: 'Lesson 31',
      title: 'Build the IELTS Speaking Part 2 Engine',
      desc: 'Created Part 2 state machine (Part2State), cue card database (cue_cards.py), Part2Controller with server-side monotonic timing (60s preparation, 120s long turn), task coverage scoring, and extended WebSocket event protocol (start_part2, part2_cue_card, start_preparation, start_long_turn).'
    },
    {
      step: 'Lesson 32',
      title: 'Build the IELTS Speaking Part 3 Engine',
      desc: 'Created Part 3 state machine (Part3State), structured topics & categories (part3_topics.py), transition matrix & question templates (templates.py), strategy & validation engine (strategy.py), and Part3Controller with idea development tracking (claim, reason, example, explanation) and hybrid Qwen follow-up reasoning under strict exam policies.'
    },
    {
      step: 'Lesson 33',
      title: 'Build the IELTS Speaking Scoring & Feedback Engine',
      desc: 'Created scoring data models (scoring/models.py), objective speech feature extraction (speech_features.py for WPM, pause breakdown, fillers, self-corrections), official band descriptor bank for Bands 5-9 (scoring/descriptors/), SpeakingScoringEngine with evidence aggregation & IELTS rounding rules (.25/.75), and personalized 7-day practice plan generator.'
    },
    {
      step: 'Lesson 34',
      title: 'Build the Real-Time Voice Pipeline',
      desc: 'Created RealtimeVADEngine with mode-specific silence thresholds (speech/vad.py), rolling pre-speech pre-roll buffer, examiner echo prevention guard (examiner_speaking), async non-blocking queue worker (speech/queue_worker.py), end-to-end latency benchmarks tracker (speech/metrics.py), and FullDuplexVoicePipeline with /ws/speaking full-duplex protocol.'
    },
    {
      step: 'Lesson 35',
      title: 'Build Your First End-to-End Voice Prototype',
      desc: 'Created full-duplex end-to-end voice loop connecting browser microphone (frontend/index.html), FastAPI WebSocket server (/ws/speaking & /prototype), Whisper Service (STT abstraction), Qwen LLM reasoning engine, and Kokoro Service (TTS audio synthesis & browser playback).'
    },
    {
      step: 'Lesson 36',
      title: 'Integrate Local Whisper for Speech-to-Text',
      desc: 'Integrated local speech recognition using faster-whisper (CTranslate2 int8/float16) with timestamp segment preservation (start, end, text), audio normalization via FFmpeg/PCM, dual fallback chain (faster-whisper -> openai-whisper -> mock engine), /transcribe endpoint, and test_whisper.py unit tests.'
    },
    {
      step: 'Lesson 37',
      title: 'Build Real-Time VAD + Speech Segmentation',
      desc: 'Created Real-Time Voice Activity Detection (VAD) & speech segmentation engine with mode-specific silence thresholds (speech_config.py), 300ms pre-roll audio buffer (audio_buffer.py), VAD state machine (vad.py), candidate session state encapsulation (sessions/session.py), and test_vad.py lifecycle tests.'
    },
    {
      step: 'Lesson 38',
      title: 'Build the IELTS Examiner Controller',
      desc: 'Implemented deterministic ExaminerController state machine (examiner/controller.py) governing exam navigation (Part 1 -> Part 2 -> Part 3), allowed actions, timing rules, candidate answer logs, and rich question bank metadata (examiner/questions.py).',
      code: `# Run ExaminerController state machine unit test
python3 backend/test_controller.py`
    },
    {
      step: 'Lesson 39',
      title: 'Connect Qwen to the IELTS Examiner Controller',
      desc: 'Connected Qwen LLM reasoning engine to ExaminerController with Pydantic schema validation (examiner/schema.py), constrained prompt generator (prompts/examiner.py), QwenService action verification (qwen_service.py), and multi-turn conversational loop integration tests.'
    },
    {
      step: 'Lesson 40',
      title: 'Connect Qwen + Ollama to Your IELTS AI',
      desc: 'Established real async connection between QwenService (using httpx / urllib) and local Ollama API (http://localhost:11434), temperature tuning (0.3), response parsing & markdown stripping (examiner/parser.py), and state transition matrix verification (examiner/transitions.py).',
      code: `# Run Qwen + Ollama API async connectivity test
python3 backend/test_qwen.py

# Run IELTS Examiner engine integration test
python3 backend/test_examiner.py`
    },
    {
      step: 'Lesson 41',
      title: 'Reliable Qwen Output + Streaming',
      desc: 'Implemented 3-level validation architecture (Prompt -> Pydantic Schema Enum -> Controller Transition Matrix) and Strategy A streaming JSON token assembly in QwenService, protecting the exam state machine against invalid actions and LLM overrides with deterministic fallbacks.',
      code: `# Run Lesson 41 3-Layer Validation & Streaming Fallback test suite
python3 backend/test_lesson41.py`
    },
    {
      step: 'Lesson 42',
      title: 'WebSocket Architecture for Real-Time Examiner',
      desc: 'Established stateful persistent WebSocket bidirectional event layer (/ws/exam and /ws/exam/{session_id}), event router protocol (session_start, speech_start, speech_end, ping -> pong, state, transcript, examiner_response), and isolated session manager supporting candidate disconnect resilience.',
      code: `# Run Lesson 42 Real-Time WebSocket Protocol test suite
python3 backend/test_lesson42.py`
    },
    {
      step: 'Lesson 43',
      title: 'Real-Time Microphone Audio Pipeline',
      desc: 'Built browser microphone capture via AudioWorkletProcessor (pcm-processor.js), Float32 to Int16 PCM little-endian (pcm_s16le) conversion, WebSocket binary frame streaming, and backend AudioBuffer session accumulation with WAV header export.',
      code: `# Run Lesson 43 Real-Time Microphone Audio Pipeline test suite
python3 backend/test_lesson43.py`
    },
    {
      step: 'Lesson 44',
      title: 'Voice Activity Detection (VAD) & Endpointing',
      desc: 'Integrated Silero & Energy VAD engines, VADSegmenter endpointing state machine with 300ms pre-roll and post-roll buffers, adaptive IELTS silence thresholds (Part 1 = 1200ms, Part 2 = 2000ms, Part 3 = 1500ms), and real-time WebSocket state notification.',
      code: `# Run Lesson 44 Real-Time Voice Activity Detection test suite
python3 backend/test_lesson44.py`
    },
    {
      step: 'Lesson 45',
      title: 'Whisper Integration (Speech → Text)',
      desc: 'Integrated faster-whisper and structured WhisperService producing Pydantic Transcript schemas with timestamps, preserving candidate raw phrasing for IELTS scoring, and connecting VAD-finalized speech audio to WebSocket transcription events.',
      code: `# Run Lesson 45 Whisper Speech-to-Text test suite
python3 backend/test_lesson45.py`
    },
    {
      step: 'Lesson 46',
      title: 'Whisper Model Selection & GPU Optimization',
      desc: 'Configured Whisper model selection via environment variables (WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE), CUDA GPU auto-detection with graceful CPU fallback (int8), warmup inference, RTF latency tracking, and 5-run benchmark suite.',
      code: `# Run Lesson 46 Whisper GPU & Benchmarking test suite
python3 backend/test_lesson46.py`
    },
    {
      step: 'Lesson 47',
      title: 'Real-Time Transcription & Partial Results',
      desc: 'Implemented partial (beam_size=1) vs final (beam_size=5) ASR streams, transcript.partial UI events without Qwen triggers, transcript.final authoritative turn submission, and 0.3s sliding window audio thresholding.',
      code: `# Run Lesson 47 Partial & Final Transcription test suite
python3 backend/test_lesson47.py`
    },
    {
      step: 'Lesson 48',
      title: 'Speech Endpointing & Conversation Turn Detection',
      desc: 'Deterministic audio-driven turn detection state machine (TurnDetector), state transitions (IDLE, LISTENING, CANDIDATE_SPEAKING, POSSIBLE_END, TURN_ENDED), dynamic IELTS Part silence thresholds, hesitation resilience, hard max duration timers, and real-time WebSocket speech turn events.',
      code: `# Run Lesson 48 Speech Endpointing & Turn Detection test suite
python3 backend/test_lesson48.py`
    },
    {
      step: 'Lesson 49',
      title: 'Kokoro TTS Integration & Voice Loop',
      desc: 'Sentence-level text-to-speech (TTS) streaming pipeline, KokoroService client integration, phrase caching for common examiner prompts, automatic synthetic WAV fallback, EXAMINER_SPEAKING state tracking, and candidate microphone echo suppression guard.',
      code: `# Run Lesson 49 Kokoro TTS Integration test suite
python3 backend/test_lesson49.py`
    },
    {
      step: 'Lesson 50',
      title: 'Connecting Whisper + Qwen + Kokoro into One Real-Time Voice Pipeline',
      desc: 'RealtimeVoiceOrchestrator connecting Whisper ASR, Examiner Controller reasoning (Qwen), and Kokoro TTS into one event-driven voice-to-voice pipeline. Includes SpeakingTurn data schema, stage-by-stage latency tracking (ASR, Qwen, TTS, total), complete WebSocket event sequence, and candidate microphone echo suppression guard.',
      code: `# Run Lesson 50 Real-Time Voice Pipeline test suite
python3 backend/test_lesson50.py`
    },
    {
      step: 'Lesson 51',
      title: 'Building the IELTS Examiner Controller',
      desc: 'Rule-based Examiner Controller state machine (FSM) acting as examination traffic controller. Manages dual states (ExaminationState + ConversationState), controlled question banks (Part 1, Part 2 Cue Cards, Part 3 Topics), defense-in-depth output validator (ExaminerOutputValidator), Part 2 timers, and Exam Mode vs Practice Mode configurations.',
      code: `# Run Lesson 51 Examiner Controller test suite
python3 backend/test_lesson51.py`
    },
    {
      step: 'Lesson 52',
      title: 'Real-Time WebSocket Architecture',
      desc: 'Established stateful full-duplex WebSocket architecture connecting browser PCM audio streaming and backend real-time loop. Enforces server authority over examination state transitions, binary audio chunk routing to AudioBuffer & TurnDetector, candidate mic echo suppression, and end-to-end latency tracking.',
      code: `# Run Lesson 52 Real-Time WebSocket Architecture test suite
python3 backend/test_lesson52.py`
    },
    {
      step: 'Lesson 53',
      title: 'Building the Real-Time Audio Pipeline',
      desc: 'RealtimeAudioPipeline managing 16kHz 16-bit Mono PCM audio capture, chunking vs speech segment vs exam turn metrics, VAD vs endpointing decision logic, candidate microphone echo suppression guard, WAV header export, turn resets, and full observability metrics (ASR, LLM, TTS, total latency).',
      code: `# Run Lesson 53 Real-Time Audio Pipeline test suite
python3 backend/test_lesson53.py`
    },
    {
      step: 'Lesson 54',
      title: 'Integrating Whisper for Real-Time Speech Recognition',
      desc: 'Whisper STT service abstraction with CUDA/CPU int8 execution, explicit English language configuration, raw transcript preservation for GRA scoring integrity, partial streaming vs authoritative final passes, warm model initialization, and benchmark latency/RTF metrics.',
      code: `# Run Lesson 54 Whisper STT test suite
python3 backend/test_lesson54.py`
    },
    {
      step: 'Lesson 55',
      title: 'Integrating Qwen as the IELTS Examiner Brain',
      desc: 'Qwen LLM integrated under the "LLM proposes; Controller decides" principle. Features System Prompt & dynamic context separation, candidate speech prompt injection defenses, single-question validation, word-count limits, and deterministic question-bank fallbacks.',
      code: `# Run Lesson 55 Qwen Examiner Brain test suite
python3 backend/test_lesson55.py`
    },
    {
      step: 'Lesson 56',
      title: 'Building the IELTS Examiner Controller & State Machine',
      desc: 'ExaminerController & ExaminerStateMachine event-driven orchestration loop. Enforces valid state transitions across INTRO, PART 1, PART 2, PART 3, and COMPLETED, server-authoritative 60s/120s timers, question deduplication, and ASR failure RECOVERY states.',
      code: `# Run Lesson 56 Examiner Controller test suite
python3 backend/test_lesson56.py`
    },
    {
      step: 'Lesson 57',
      title: 'Integrating Kokoro TTS for Natural Examiner Voice',
      desc: 'KokoroTTSService abstraction converting examiner text into clean 24kHz Mono WAV speech. Features metadata duration tracking, sentence-level streaming synthesis helpers, and TTS playback timing guards to protect against microphone echo feedback.',
      code: `# Run Lesson 57 Kokoro TTS test suite
python3 backend/test_lesson57.py`
    },
    {
      step: 'Lesson 58',
      title: 'Real-Time WebSocket Voice Communication',
      desc: 'WebSocketManager persistent session loop connecting Browser mic <-> VAD <-> Whisper STT <-> ExaminerController <-> Qwen LLM <-> Kokoro TTS. Enforces server-authoritative state control, ping/pong heartbeats, echo suppression during examiner speech, and disconnect reconnection recovery.',
      code: `# Run Lesson 58 Real-Time WebSocket test suite
python3 backend/test_lesson58.py`
    },
    {
      step: 'Lesson 59',
      title: 'Complete Local AI IELTS Examiner Architecture',
      desc: 'Integrated full 6-Layer architecture: Frontend UI, Real-Time WebSocket Channel (/ws/exam), Server-Authoritative ExaminerController, AI Pipeline (Whisper + Qwen + Kokoro), Session Persistence & Scoring Engine, and Infrastructure Health Check.',
      code: `# Run Lesson 59 6-Layer Architecture test suite
PYTHONPATH=backend python3 backend/test_lesson59.py`
    },
    {
      step: 'Lesson 60',
      title: 'Final Production Blueprint & System Completion',
      desc: 'Course completion milestone (60/60). Full system verification across all 6 layers, 46 unit tests, Docker containerization blueprint, production migration roadmap, security, privacy, and latency budgets.',
      code: `# Run complete 60-lesson backend test suite across all 46 test modules
PYTHONPATH=backend python3 -m unittest discover -s backend -p "test_lesson*.py"`
    }
  ];



  const dockerComposeCode = `version: '3.8'

services:
  # 1. Local LLM Service (Ollama)
  ollama:
    image: ollama/ollama:latest
    container_name: ielts_ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_storage:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: always

  # 2. Text-to-Speech Service (Kokoro)
  kokoro-tts:
    image: ghcr.io/kokoro-tts/kokoro-fastapi:latest
    container_name: ielts_kokoro
    ports:
      - "8880:8880"
    environment:
      - DEVICE=cuda
      - DEFAULT_VOICE=af_heart
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: always

  # 3. IELTS Backend API (FastAPI + SQLite + Whisper + Examiner Engine + Memory + SessionManager)
  fastapi-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ielts_fastapi
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_URL=http://ollama:11434
      - KOKORO_URL=http://kokoro-tts:8880
      - MODEL_NAME=qwen3:8b
    depends_on:
      - ollama
      - kokoro-tts
    restart: always

volumes:
  ollama_storage:`;

  return (
    <div className="space-y-6 my-6">
      
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-emerald-950 to-slate-900 border border-emerald-500/30 rounded-2xl p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <span className="px-3 py-1 text-xs font-bold rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center">
                <Server className="w-3.5 h-3.5 mr-1" />
                Lessons 1 – 60 Complete Guide (60/60 ✅)
              </span>

              <span className="text-xs text-slate-400">Local AI Stack: Ollama + Whisper STT + Kokoro TTS + SQLite + Silero VAD + Speech Segmenter + Turn Detector + Examiner Brain + Qwen Evaluation</span>
            </div>
            <h2 className="text-2xl font-black text-white">IELTS Speaking AI — Complete A to Z Setup Guide</h2>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl leading-relaxed">
              Exhaustive step-by-step local installation guide covering environment setup, model downloads, SQLite session database creation, IELTS Examiner Engine, Real-Time VAD Voice Conversation, Automatic Evaluator Engine, End-to-End MVP, React Browser Mic, Whisper STT, Qwen Multi-Turn Examiner, Kokoro TTS speech synthesis, Silero VAD, real-time WebSocket streaming, 16kHz PCM streaming, 5-state speech segmentation, Whisper STT segment transcription, Examiner Brain, and Qwen Evaluation Engine.
            </p>
          </div>

          <div className="bg-slate-950/80 p-4 rounded-xl border border-emerald-500/30 text-xs space-y-1">
            <div className="text-emerald-400 font-bold flex items-center">
              <ShieldCheck className="w-4 h-4 mr-1" /> 100% Private & Local
            </div>
            <p className="text-slate-400 text-[11px]">Saved in <code className="text-emerald-300 font-mono">LOCAL_SETUP_GUIDE.md</code> in source code.</p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex flex-wrap gap-2 bg-slate-900 p-1.5 rounded-xl border border-slate-800">
        {[
          { id: 'a-to-z', label: '1. A to Z Lessons 1–60 Master Guide', icon: BookOpen },

          { id: 'architecture', label: '2. Examiner, Evaluator, Whisper & Qwen Architecture', icon: Layers },
          { id: 'code', label: '3. Docker & Backend Code', icon: Code },
          { id: 'hardware', label: '4. Hardware & VRAM Guide', icon: Cpu },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                isActive
                  ? 'bg-emerald-600 text-white shadow-md'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: A to Z Lessons Roadmap */}
      {activeTab === 'a-to-z' && (
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white flex items-center">
                <Terminal className="w-5 h-5 text-emerald-400 mr-2" />
                Step-by-Step Local Command Guide (Lessons 1 – 20)
              </h3>
              <div className="flex items-center space-x-1.5 text-xs text-emerald-300 bg-emerald-950/80 px-3 py-1 rounded-lg border border-emerald-500/30">
                <FileText className="w-3.5 h-3.5" />
                <span>See LOCAL_SETUP_GUIDE.md</span>
              </div>
            </div>
            <p className="text-xs text-slate-400 mb-6">
              Run these commands in your local terminal sequentially to build and launch the complete IELTS Speaking AI system from scratch.
            </p>

            <div className="space-y-4">
              {aToZSteps.map((s, idx) => (
                <div key={idx} className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="px-2.5 py-0.5 text-[10px] font-bold rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                        {s.step}
                      </span>
                      <h4 className="font-bold text-white text-sm">{s.title}</h4>
                    </div>
                  </div>
                  <p className="text-xs text-slate-400">{s.desc}</p>
                  
                  <div className="bg-slate-900 p-3 rounded-lg border border-slate-800 font-mono text-xs text-emerald-300 flex items-center justify-between overflow-x-auto">
                    <pre className="text-[11px] leading-relaxed">{s.code}</pre>
                    <button
                      onClick={() => handleCopy(s.code, `atoz-${idx}`)}
                      className="text-slate-400 hover:text-white ml-2 p-1 rounded shrink-0"
                    >
                      {copiedIndex === `atoz-${idx}` ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Architecture */}
      {activeTab === 'architecture' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
          <h3 className="text-lg font-bold text-white flex items-center">
            <Layers className="w-5 h-5 text-emerald-400 mr-2" />
            Whisper → IELTS Engine → Qwen Examiner Architecture (Lessons 19 & 20)
          </h3>

          <div className="bg-slate-950 p-6 rounded-xl border border-slate-800 font-mono text-xs text-slate-200 overflow-x-auto leading-relaxed">
            <pre className="text-emerald-300">{`
┌─────────────────────────────────────────────────────────────────────────────┐
│                       IELTS SPEAKING MULTI-TURN AI                          │
│                                                                             │
│    🎤 Student (Browser Mic)                                                  │
│         │                                                                   │
│         ▼                                                                   │
│    WebSocket (ws://localhost:8000/ws/speaking/SESSION_ID)                   │
│         │                                                                   │
│         ▼                                                                   │
│    FastAPI WebM Storage -> FFmpeg -> 16kHz WAV                              │
│         │                                                                   │
│         ▼                                                                   │
│    Whisper STT Engine (small/medium) ──► Candidate Transcript               │
│         │                                                                   │
│         ▼                                                                   │
│    IELTS Test Engine (Deterministic Rules & Question State)                 │
│         │                                                                   │
│         ▼                                                                   │
│    Conversation Memory + Answer Storage in SQLite                           │
│         │                                                                   │
│         ▼                                                                   │
│    Qwen LLM Examiner Service (Natural Question Phrasing)                    │
│         │                                                                   │
│         ▼                                                                   │
│    Kokoro TTS / Browser Voice Audio Output                                  │
│         │                                                                   │
│         ▼                                                                   │
│    🔊 Student hears Examiner Question                                       │
└─────────────────────────────────────────────────────────────────────────────┘
            `}</pre>
          </div>
        </div>
      )}

      {/* Tab 3: Docker & Backend Code */}
      {activeTab === 'code' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Code className="w-4 h-4 text-emerald-400" />
                <span className="font-bold text-white text-sm">docker-compose.yml</span>
              </div>
              <button
                onClick={() => handleCopy(dockerComposeCode, 'docker')}
                className="flex items-center space-x-1 text-xs bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-3 py-1.5 rounded-lg transition-colors"
              >
                {copiedIndex === 'docker' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedIndex === 'docker' ? 'Copied!' : 'Copy YAML'}</span>
              </button>
            </div>
            <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 font-mono text-xs text-slate-200 overflow-x-auto max-h-80">
              {dockerComposeCode}
            </pre>
          </div>
        </div>
      )}

      {/* Tab 4: Hardware Calculator */}
      {activeTab === 'hardware' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center">
              <Cpu className="w-5 h-5 text-emerald-400 mr-2" />
              Interactive Local VRAM / Hardware Estimator
            </h3>
            <div className="flex items-center space-x-3 my-4">
              <label className="text-xs font-bold text-slate-300">Your GPU VRAM:</label>
              {[8, 12, 16, 24].map((gb) => (
                <button
                  key={gb}
                  onClick={() => setSelectedVram(gb)}
                  className={`px-4 py-2 rounded-xl text-xs font-bold border transition-all ${
                    selectedVram === gb
                      ? 'bg-emerald-600 text-white border-emerald-500 shadow-md'
                      : 'bg-slate-800 text-slate-300 border-slate-700 hover:bg-slate-700'
                  }`}
                >
                  {gb} GB VRAM
                </button>
              ))}
            </div>

            <div className="bg-slate-950 p-5 rounded-xl border border-emerald-500/30 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-bold">Recommended LLM</span>
                <div className="text-sm font-bold text-emerald-300 mt-0.5">
                  {selectedVram >= 24 ? 'Qwen 3 (32B) / Llama 3.1 (70B)' : selectedVram >= 16 ? 'Qwen 3 (14B)' : 'Qwen 3 (8B)'}
                </div>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-bold">Recommended Speech STT</span>
                <div className="text-sm font-bold text-sky-300 mt-0.5">
                  {selectedVram >= 24 ? 'faster-whisper (large-v3)' : 'faster-whisper (small/medium)'}
                </div>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-bold">Concurrent Students</span>
                <div className="text-sm font-bold text-amber-300 mt-0.5">
                  {selectedVram >= 24 ? '8 - 12 Simultaneous Tests' : '1 Single Active Test'}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
};
