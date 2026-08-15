# AI IELTS Speaking Pro — System Architecture & Functional Design

This document provides a comprehensive technical and functional breakdown of the **AI IELTS Speaking Pro** platform. It outlines how every subsystem interacts—from microphone audio capture and Speech-to-Text (STT) to Large Language Model (LLM) reasoning, Text-to-Speech (TTS) synthesis, and structured persistence.

---

## 1. High-Level System Architecture

```
+-----------------------------------------------------------------------------------+
|                                CLIENT BROWSER (React)                             |
|                                                                                   |
|  +---------------------+   +---------------------+   +-------------------------+  |
|  |   Candidate Voice   |   |   Live Audio VAD    |   |     Stage Controller    |  |
|  |  (MediaDevices Mic) |-->| (Web Audio Energy)  |-->| (Part 1 / Part 2 / 3)   |  |
|  +---------------------+   +---------------------+   +-------------------------+  |
|             |                                                     ^               |
|             v                                                     |               |
|  +---------------------+                             +-------------------------+  |
|  |  PCM 16kHz Streamer |                             |  Examiner Audio Player  |  |
|  |   (WebSocket/REST)  |                             | (Kokoro WAV / WebAudio) |  |
|  +---------------------+                             +-------------------------+  |
+-------------|-----------------------------------------------------^---------------+
              |                                                     |
              v                                                     |
+-------------------------------------------------------------------|---------------+
|                       BACKEND / API ORCHESTRATION LAYER           |               |
|                 (Express / Vite Proxy on :3000 & FastAPI on :8000)|               |
|                                                                   |               |
|  +----------------------------------------------------------------+------------+  |
|  |                          ROUTER & FAILOVER PIPELINE                         |  |
|  |                                                                             |  |
|  |   [ STT Service ]             [ LLM Examiner Brain ]         [ TTS Engine ] |  |
|  |   1. Faster-Whisper (Local)   1. Ollama Qwen2.5/Qwen3 (Local)1. Kokoro TTS  |  |
|  |   2. Browser Speech Fallback  2. Gemini 2.5 Flash (Cloud)    2. Web Speech  |  |
|  |                               3. Cambridge Rules Bank        Synthesis      |  |
|  +-----------------------------------------------------------------------------+  |
|                                         |                                         |
|                                         v                                         |
|  +-----------------------------------------------------------------------------+  |
|  |                    DATABASE & STATE PERSISTENCE LAYER                       |  |
|  |     - SQLite Session Store (`backend/database.py`)                          |  |
|  |     - Dynamic Cambridge Question Banks (`src/services/questionBankLoader`)  |  |
|  |     - Candidate 9-Band Diagnostic Assessment Records                        |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Core Subsystems & Component Roles

### 🎤 1. Speech-to-Text (STT) Role
* **Primary Implementation**: `backend/whisper_engine.py` / `backend/whisper_service.py` (Faster-Whisper running `base.en` / `small.en`).
* **Fallback Implementation**: Client-side Speech Recognition & Base64 Audio Transcription API.
* **Role**:
  - Captures raw candidate vocalizations sampled at 16kHz mono PCM.
  - Converts acoustic speech waves into precise text strings.
  - Generates speech timing metrics (word counts, pauses, utterance duration) used to score **Fluency & Coherence**.
* **Concrete Example**:
  > *Candidate speaks*: *"Well, honestly speaking, I've lived in Manchester for roughly five years."*  
  > *STT Output*: `"Well, honestly speaking, I've lived in Manchester for roughly five years."` (Duration: 3.8s, Words: 12, Speech Rate: 189 WPM).

---

### 🧠 2. LLM / Examiner Brain Role (Ollama & Gemini)
* **Primary Implementation**: `backend/qwen_engine.py`, `backend/examiner_engine.py` (Local **Ollama Qwen2.5-7B-Instruct** / **Qwen3**).
* **Cloud & Server Proxy Integration**: `server.ts` via `@google/genai` (**Gemini 2.5 Flash**).
* **Deterministic Fallback**: Structured Cambridge IELTS Question Banks (`src/data/` and `src/services/questionBankLoader.ts`).
* **Roles**:
  1. **Conversational Turn Generation**: Evaluates what the candidate just said and selects or formulates the next authentic examiner question without conversational drift.
  2. **Part Control**:
     - **Part 1**: Short, direct introduction questions (Hometown, Work/Study, Hobbies).
     - **Part 2**: Manages 1-minute cue card prep and ensures candidate speaks for 1–2 minutes.
     - **Part 3**: Generates abstract, probing analytical follow-ups based on the candidate's Part 2 topic.
  3. **Live Training Feedback**: In **Training Mode**, produces immediate Band 8.0+ grammar fixes and advanced lexical collocations.
  4. **Diagnostic Scoring Engine**: At test completion, evaluates the full transcript against official British Council / IDP 9-band descriptors.
* **Concrete Example (Examiner Generation)**:
  > *Candidate*: *"I work in software engineering, mostly building web apps."*  
  > *LLM Output*:
  > ```json
  > {
  >   "examinerResponse": "Do you think technology will significantly change the way people do your job in the future?",
  >   "corrections": {
  >     "originalText": "I work in software engineering, mostly building web apps.",
  >     "correctedText": "I am currently employed as a software engineer, specializing primarily in web application development.",
  >     "vocabularyUpgrades": [
  >       { "original": "mostly building", "upgraded": "specializing primarily in", "context": "Band 8.0+ formal precision" }
  >     ]
  >   }
  > }
  > ```

---

### 🔊 3. Text-to-Speech (TTS) Role
* **Primary Implementation**: `backend/kokoro_engine.py` / `backend/tts.py` (**Kokoro-82M** high-fidelity neural TTS).
* **Fallback Implementation**: Browser Web Speech Synthesis API (`window.speechSynthesis`) with British (`en-GB`) and American (`en-US`) neural voice selection.
* **Role**:
  - Converts text generated by the examiner into lifelike, human-sounding speech.
  - Implements authentic British (`bm_george`, `bf_emma`) and American (`am_michael`, `af_sarah`) examiner personas.
  - Streams WAV/PCM audio chunks to the frontend with minimal time-to-first-byte (TTFB).
* **Concrete Example**:
  > *Input Text*: *"Let's move on to Part 2. I will give you a cue card..."*  
  > *Output*: 24kHz Mono WAV stream played via Web Audio buffer, simulating a realistic British Council examiner.

---

### 🎚️ 4. Voice Activity Detection (VAD) & Audio Pipeline
* **Primary Implementation**: `src/hooks/useVAD.ts` and `src/audio/PCMStreamer.ts`.
* **Role**:
  - Continuous real-time audio volume and RMS energy tracking.
  - Automatically identifies when the candidate starts speaking and when they stop (1.5 seconds of silence).
  - Enforces official IELTS speaking safety limits (60 seconds for Part 1/Part 3 questions; 120 seconds for Part 2 Long Turn).
  - Eliminates the need for manual button tapping, creating a natural interview rhythm.

---

### 🗄️ 5. Database & State Persistence Role
* **Primary Implementation**:
  - `backend/database.py` / `backend/models.py` (SQLite with SQLAlchemy ORM).
  - `src/services/questionBankLoader.ts` (Dynamic Cambridge JSON Bank).
  - Browser `localStorage` (Session transcript recovery & active test state).
* **Role**:
  - Stores complete conversation transcripts, turn timestamps, and audio metrics.
  - Persists custom uploaded Cambridge Question Banks (Part 1, Part 2 Cue Cards, Part 3).
  - Archives final IELTS Band Diagnostic Reports (Overall Band, 4 Criteria Scores, 7-day study plans).
* **Concrete Example (Stored Assessment Record)**:
  ```json
  {
    "sessionId": "mock-ielts-20260815-01",
    "overallBand": 7.5,
    "scores": {
      "fluencyScore": 7.5,
      "lexicalScore": 8.0,
      "grammarScore": 7.0,
      "pronunciationScore": 7.5
    },
    "keyStrengths": ["Natural discourse markers", "Wide lexical flexibility"],
    "priorityImprovements": ["Conditional clause variety under pressure"]
  }
  ```

---

### 💻 6. Frontend UI & State Controller Role
* **Primary Implementation**: `src/App.tsx`, `src/components/*` (React 18 + Tailwind CSS + Lucide Icons).
* **Role**:
  - **Exam Stage Selector**: Manages test progression (`part1` $\rightarrow$ `part2` $\rightarrow$ `part3` $\rightarrow$ `completed`).
  - **Cue Card Viewer**: Dedicated 1-minute countdown note-taking scratchpad and bullet-point cue display.
  - **Band Report View**: Interactive diagnostic scorecard with breakdown charts, grammar critique, and a customized 7-day study schedule.
  - **Local Deployment Modal**: Built-in instructions and health monitoring for local Docker, Ollama, Whisper, and Kokoro configurations.

---

## 3. End-to-End Execution Flow (Single Spoken Turn)

```
Candidate Speaks into Mic
          │
          ▼
[1] Web Audio VAD detects voice start -> Begins streaming PCM 16kHz
          │
[2] Candidate pauses for 1.5s -> VAD triggers turn completion
          │
          ▼
[3] STT Engine (Faster-Whisper / Audio API) converts speech to text
          │
          ▼
[4] Examiner Brain (Qwen2.5 / Gemini / Question Bank) processes context:
    - Formulates next question
    - Computes real-time Band 8.0+ corrections (in Training Mode)
          │
          ▼
[5] TTS Engine (Kokoro-82M / Web Speech) synthesizes examiner speech
          │
          ▼
[6] Frontend plays examiner audio & updates real-time transcript
          │
          ▼
[7] Session state & metrics stored in database / local cache
```

---

## 4. Resilience & Fallback Matrix

| Subsystem | Primary Local Layer | Cloud / Remote Proxy Layer | Zero-Dependency Fallback |
| :--- | :--- | :--- | :--- |
| **STT** | Faster-Whisper (`base.en` / `small.en`) on `:8000` | Backend Base64 Whisper Proxy | Web Speech Recognition API |
| **LLM** | Ollama Qwen2.5-7B (`http://localhost:11434`) | Google Gemini 2.5 Flash (`@google/genai`) | Cambridge Topic Matrix & Fallback Logic |
| **TTS** | Kokoro-82M Neural Model on `:8000` | Streaming WAV Chunk API | Browser Neural `SpeechSynthesis` (`en-GB` / `en-US`) |
| **Storage** | SQLite Database (`backend/database.py`) | Server Session Cache | Browser `localStorage` & In-Memory State |

This tiered architecture ensures that the application operates at maximum performance when full local hardware acceleration (NVIDIA GPU / Metal) is present, while remaining 100% operational in browser-only, cloud, or offline demonstration environments.
