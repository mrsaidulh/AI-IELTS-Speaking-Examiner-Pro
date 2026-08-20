# Production Deployment & Infrastructure Sizing Guide
## Supporting 20+ Concurrent Active Voice IELTS Test Candidates

This document details the exact hardware requirements, system architecture, database configurations, and step-by-step instructions to deploy **AI IELTS Speaking Pro** into a production environment capable of smoothly supporting **20 simultaneous real-time voice examinees**.

---

## 1. Concurrency & Workload Math for 20 Active Voice Sessions

In a 15-minute IELTS Speaking test, the candidate and examiner take turns:
- **~50% of the time (10 students simultaneously)**: Candidates are actively speaking (transmitting 16 kHz PCM audio chunks over WebSockets $\rightarrow$ VAD $\rightarrow$ Whisper STT).
- **~15% of the time (3 students simultaneously)**: Candidates finished speaking and await the LLM examiner response generation (Ollama Qwen2.5/Qwen3 or Gemini Flash).
- **~35% of the time (7 students simultaneously)**: Examiner TTS is generating/streaming audio back (Kokoro TTS $\rightarrow$ Web Audio playback).

| Pipeline Stage | Active Load at Peak | Latency Target | Resource Utilization per Request |
| :--- | :--- | :--- | :--- |
| **WebSocket / Ingress** | 20 persistent connections | < 15ms ping | ~5.2 Mbps aggregate network bandwidth |
| **Whisper STT** | 5–10 concurrent transcribes | < 350ms per turn | ~1.5 GB VRAM (Faster-Whisper `base.en`/`small.en`) |
| **LLM Inference** | 3–4 parallel text gens | < 600ms per turn | ~6–8 GB VRAM (Qwen2.5-7B 4-bit) or 0 GPU with Gemini API |
| **Kokoro-82M TTS** | 2–4 parallel syntheses | < 250ms per turn | ~1.5 GB VRAM / 2 CPU cores |
| **Database** | ~40 writes/min | < 5ms query | PostgreSQL connection pool (25–50 pool size) |

---

## 2. Recommended Hardware Specifications

### Option A: Dedicated Single GPU Server (Self-Hosted / Cloud VPS) — *Most Cost-Effective*
Best suited for running the entire stack (Whisper + Qwen LLM + Kokoro + FastAPI + PostgreSQL + React) on one dedicated machine.

| Component | Minimum Specification | Recommended Specification |
| :--- | :--- | :--- |
| **GPU** | 1x NVIDIA RTX 3090 (24GB) or A10G (24GB) | 1x NVIDIA RTX 4090 (24GB) or L4 / A100 (24–40GB) |
| **CPU** | 8 Cores / 16 Threads (AMD EPYC or Intel Xeon) | 16 Cores / 32 Threads |
| **RAM** | 32 GB DDR4/DDR5 | 64 GB DDR5 |
| **Storage** | 100 GB NVMe SSD | 250 GB NVMe SSD (fast model caching) |
| **Network** | 100 Mbps symmetric bandwidth | 1 Gbps symmetric with SSL / TLS termination |
| **Est. Cloud Cost** | ~$150 – $220 / month (RunPod, Vast.ai, Hetzner, Lambda) | ~$250 – $350 / month (AWS g5.2xlarge, GCP g2-standard-8) |

---

### Option B: Cloud Hybrid Architecture (Zero-GPU Server + Gemini API) — *Easiest & Most Scalable*
Offloads the LLM reasoning to the Google Gemini API, running only Whisper STT and Kokoro TTS locally or on a low-cost GPU / CPU instance.

| Layer | Technology | Sizing for 20 Students |
| :--- | :--- | :--- |
| **LLM Examiner Brain** | Google Gemini 2.5 Flash | Infinite scaling, 0 VRAM requirement (~$0.0002 / test) |
| **STT + TTS Server** | 1x NVIDIA T4 (16GB) or RTX 3060 (12GB) | Handles 20+ concurrent Whisper & Kokoro audio streams |
| **Web & App Server** | 4 vCPU, 8 GB RAM VPS | Handles Nginx, Express, FastAPI, and PostgreSQL |
| **Est. Cloud Cost** | ~$40 – $80 / month | Total operational cost |

---

## 3. Production Architecture Diagram

```
                             [ 20 Concurrent Candidates (Browser / Mobile) ]
                                                   │
                                     HTTPS / WSS (Port 443)
                                                   │
                                                   ▼
                                        ┌─────────────────────┐
                                        │ NGINX Reverse Proxy │
                                        │   SSL Termination   │
                                        │ Rate Limit & Gzip   │
                                        └──────────┬──────────┘
                                                   │
                         ┌─────────────────────────┴─────────────────────────┐
                         │                                                   │
                         ▼ (Static / React App)                              ▼ (WebSocket / REST :8000)
               ┌───────────────────┐                               ┌───────────────────┐
               │   Frontend SPA    │                               │  FastAPI Backend  │
               │   (Nginx / CDN)   │                               │ (Gunicorn Workers)│
               └───────────────────┘                               └─────────┬─────────┘
                                                                             │
                      ┌──────────────────────────────┬───────────────────────┴──────────────────────┐
                      ▼                              ▼                                              ▼
            ┌──────────────────┐           ┌──────────────────┐                           ┌──────────────────┐
            │  Faster-Whisper  │           │   Kokoro-82M     │                           │   LLM Engine     │
            │   Worker Pool    │           │    FastAPI       │                           │ 1. Ollama (Local)│
            │  (CUDA / CTrans) │           │   (Port 8880)    │                           │ 2. Gemini Flash  │
            └──────────────────┘           └──────────────────┘                           └──────────────────┘
                      │                              │                                              │
                      └──────────────────────────────┼──────────────────────────────────────────────┘
                                                     ▼
                                       ┌───────────────────────────┐
                                       │   PostgreSQL + Redis      │
                                       │   (Session DB + Cache)    │
                                       └───────────────────────────┘
```

---

## 4. Step-by-Step Production Deployment Guide

### Step 1: Install NVIDIA Drivers & Container Toolkit
On Ubuntu 22.04 / 24.04 LTS:

```bash
# Update system
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git build-essential ffmpeg libpq-dev

# Install NVIDIA Container Toolkit (for Docker GPU passthrough)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt update
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

---

### Step 2: Configure PostgreSQL for Multi-User Sessions

Create the production database:
```bash
sudo apt install -y postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE USER ielts_user WITH PASSWORD 'SecurePassword123!';"
sudo -u postgres psql -c "CREATE DATABASE ielts_production OWNER ielts_user;"
```

Update `backend/.env`:
```env
DATABASE_URL=postgresql://ielts_user:SecurePassword123!@localhost:5432/ielts_production
OLLAMA_NUM_PARALLEL=4
OLLAMA_MAX_LOADED_MODELS=1
GEMINI_API_KEY=your_production_gemini_key_if_using_cloud_fallback
```

---

### Step 3: Production Docker Compose Setup (`docker-compose.prod.yml`)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    restart: always
    environment:
      POSTGRES_USER: ielts_user
      POSTGRES_PASSWORD: SecurePassword123!
      POSTGRES_DB: ielts_production
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  ollama:
    image: ollama/ollama:latest
    restart: always
    environment:
      - OLLAMA_NUM_PARALLEL=4
      - OLLAMA_MAX_LOADED_MODELS=1
    volumes:
      - ollama_models:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    ports:
      - "11434:11434"

  kokoro:
    image: ghcr.io/remsky/kokoro-fastapi-gpu:latest
    restart: always
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    ports:
      - "8880:8880"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    restart: always
    command: gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --timeout 120
    environment:
      - DATABASE_URL=postgresql://ielts_user:SecurePassword123!@postgres:5432/ielts_production
      - OLLAMA_HOST=http://ollama:11434
      - KOKORO_HOST=http://kokoro:8880
    depends_on:
      - postgres
      - ollama
      - kokoro
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    ports:
      - "8000:8000"

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    restart: always
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  pgdata:
  ollama_models:
```

---

### Step 4: Nginx Production Configuration (SSL + WebSockets)

Install and configure Nginx (`/etc/nginx/sites-available/ielts-speaking.conf`):

```nginx
# Upstream clusters
upstream backend_api {
    server 127.0.0.1:8000;
    keepalive 32;
}

upstream frontend_app {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL certificates (Let's Encrypt / Certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Buffer & Timeout optimizations for 20+ voice streams
    client_max_body_size 50M;
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;

    # Frontend SPA
    location / {
        proxy_pass http://frontend_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # REST API endpoints
    location /api/ {
        proxy_pass http://backend_api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Real-Time WebSocket Streaming (/ws/exam, /ws/speaking)
    location /ws/ {
        proxy_pass http://backend_api/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }
}
```

Enable site & get free SSL:
```bash
sudo ln -s /etc/nginx/sites-available/ielts-speaking.conf /etc/nginx/sites-enabled/
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
sudo systemctl reload nginx
```

---

## 5. Performance Tuning & Concurrency Checklist

- [x] **Ollama Parallel Contexts**: Set `OLLAMA_NUM_PARALLEL=4` so Ollama handles multiple simultaneous questions without queuing.
- [x] **Whisper Model Sizing**: Use `faster-whisper` with `small.en` or `base.en` and `compute_type="float16"` or `"int8_float16"`. (A 5-second candidate response transcribes in under 120ms).
- [x] **Kokoro Voice Caching**: Enable audio chunk streaming or in-memory caching for standard opening prompts (e.g. Part 1 greetings and Part 2 instructions).
- [x] **Uvicorn Worker Scaling**: Run 4 Uvicorn workers (`-w 4`) behind Gunicorn to prevent long computations from blocking WebSocket heartbeats.
- [x] **Database Indexing**: Ensure `session_id` and `student_id` have B-tree indexes on `answers`, `transcripts`, and `evaluations` tables.
- [x] **Client-Side VAD Guard**: The Web Audio VAD in `src/hooks/useVAD.ts` suppresses background silence before transmission, reducing backend audio traffic by ~60%.
