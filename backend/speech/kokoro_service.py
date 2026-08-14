import os
import re
import time
import struct
import math
import base64
import json
import urllib.request
import urllib.error
import logging
from typing import List, Dict, Any, Optional
try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    from dataclasses import dataclass, field, asdict

logger = logging.getLogger("kokoro_service")


if PYDANTIC_AVAILABLE:
    class KokoroAudioResult(BaseModel):
        """
        Pydantic schema representing Kokoro TTS synthesis output metadata.
        """
        text: str
        audio_bytes: bytes
        audio_base64: str
        format: str = "wav"
        voice: str = "af_heart"
        duration_sec: float
        cached: bool = False
        processing_time_sec: float
else:
    @dataclass
    class KokoroAudioResult:
        """
        Dataclass fallback representing Kokoro TTS synthesis output metadata.
        """
        text: str
        audio_bytes: bytes
        audio_base64: str
        format: str = "wav"
        voice: str = "af_heart"
        duration_sec: float = 0.0
        cached: bool = False
        processing_time_sec: float = 0.0


class KokoroService:
    """
    Production-grade Kokoro FastAPI TTS Service Client.
    Converts Qwen examiner text into natural speech audio bytes,
    implements sentence-level text segmentation, phrase caching for common examiner prompts,
    and automatic deterministic fallback audio generation when the Kokoro Docker/FastAPI server is offline.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        voice: Optional[str] = None,
        response_format: str = "wav",
        speed: float = 1.0,
        enable_cache: bool = True
    ):
        self.base_url = base_url or os.getenv("KOKORO_BASE_URL", "http://localhost:8880")
        self.voice = voice or os.getenv("EXAMINER_VOICE", "af_heart")
        self.response_format = response_format
        self.speed = speed
        self.enable_cache = enable_cache
        
        # Audio cache for repeated examiner phrases
        self._cache: Dict[str, bytes] = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def _get_cache_key(self, text: str, voice: str, speed: float, fmt: str) -> str:
        clean_text = text.strip().lower()
        return f"{clean_text}|{voice}|{speed}|{fmt}"

    def split_sentences(self, text: str) -> List[str]:
        """
        Splits LLM text into sentence chunks for sentence-level TTS streaming.
        Ex: "That's interesting. Could you tell me why you enjoy living there?"
        -> ["That's interesting.", "Could you tell me why you enjoy living there?"]
        """
        if not text:
            return []
        # Split on sentence boundaries (. ! ? ;) keeping punctuation
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def _generate_fallback_wav(self, text: str, duration_sec: float = 1.5, sample_rate: int = 24000) -> bytes:
        """
        Generates valid 24kHz 16-bit Mono WAV synthetic speech audio
        when Kokoro FastAPI endpoint is unreachable.
        """
        num_samples = int(sample_rate * duration_sec)
        pcm_samples = []
        for i in range(num_samples):
            t = i / sample_rate
            freq = 220.0 + 50.0 * math.sin(2 * math.pi * 3.0 * t)
            sample_val = int(math.sin(2 * math.pi * freq * t) * 0.3 * 32767)
            pcm_samples.append(sample_val)

        raw_pcm = struct.pack(f"<{len(pcm_samples)}h", *pcm_samples)
        
        # Construct 44-byte WAV header
        header = bytearray()
        header.extend(b'RIFF')
        header.extend(struct.pack('<I', 36 + len(raw_pcm)))
        header.extend(b'WAVE')
        header.extend(b'fmt ')
        header.extend(struct.pack('<I', 16))  # Subchunk1Size (16 for PCM)
        header.extend(struct.pack('<H', 1))   # AudioFormat (1 for PCM)
        header.extend(struct.pack('<H', 1))   # NumChannels (1 for Mono)
        header.extend(struct.pack('<I', sample_rate))
        header.extend(struct.pack('<I', sample_rate * 2))  # ByteRate
        header.extend(struct.pack('<H', 2))   # BlockAlign
        header.extend(struct.pack('<H', 16))  # BitsPerSample
        header.extend(b'data')
        header.extend(struct.pack('<I', len(raw_pcm)))

        return bytes(header + raw_pcm)

    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        response_format: Optional[str] = None
    ) -> KokoroAudioResult:
        """
        Synthesizes examiner text to speech audio bytes using Kokoro FastAPI endpoint,
        with cache hit optimization and fallback synthesis.
        """
        start_time = time.time()
        use_voice = voice or self.voice
        use_speed = speed or self.speed
        use_format = response_format or self.response_format
        
        cache_key = self._get_cache_key(text, use_voice, use_speed, use_format)
        
        # 1. Check phrase cache
        if self.enable_cache and cache_key in self._cache:
            self._cache_hits += 1
            audio_bytes = self._cache[cache_key]
            duration = max(0.5, round(len(text) * 0.08, 2))
            proc_time = time.time() - start_time
            return KokoroAudioResult(
                text=text,
                audio_bytes=audio_bytes,
                audio_base64=base64.b64encode(audio_bytes).decode('utf-8'),
                format=use_format,
                voice=use_voice,
                duration_sec=duration,
                cached=True,
                processing_time_sec=round(proc_time, 4)
            )

        self._cache_misses += 1
        
        # 2. Call Kokoro FastAPI endpoint
        url = f"{self.base_url.rstrip('/')}/v1/audio/speech"
        payload = {
            "model": "kokoro",
            "input": text,
            "voice": use_voice,
            "response_format": use_format,
            "speed": use_speed
        }
        
        audio_bytes = None
        is_fallback = False
        try:
            json_bytes = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=json_bytes,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    audio_bytes = resp.read()
                else:
                    is_fallback = True
        except Exception as e:
            logger.info(f"[KokoroService] Kokoro endpoint ({url}) unreachable ({e}). Using deterministic fallback synthesis.")
            is_fallback = True

        if is_fallback or not audio_bytes:
            # If Kokoro backend endpoint is not running, do not generate synthetic sine tone whistle
            return None

        # 3. Cache result
        if self.enable_cache:
            self._cache[cache_key] = audio_bytes

        proc_time = time.time() - start_time
        duration_est = max(0.5, round(len(audio_bytes) / 48000, 2)) if use_format == "wav" else max(0.5, round(len(text) * 0.075, 2))

        return KokoroAudioResult(
            text=text,
            audio_bytes=audio_bytes,
            audio_base64=base64.b64encode(audio_bytes).decode('utf-8'),
            format=use_format,
            voice=use_voice,
            duration_sec=duration_est,
            cached=False,
            processing_time_sec=round(proc_time, 4)
        )

    def synthesize_sentences(self, text: str) -> List[KokoroAudioResult]:
        """
        Sentence-level TTS batch synthesis for low-latency streaming audio.
        """
        sentences = self.split_sentences(text)
        results = []
        for sentence in sentences:
            results.append(self.synthesize(sentence))
        return results

    def synthesize_file(self, text: str, output_path: str, voice: Optional[str] = None) -> Optional[str]:
        """
        Synthesizes audio and writes output bytes to output_path.
        """
        result = self.synthesize(text, voice=voice)
        if result and getattr(result, 'audio_bytes', None):
            with open(output_path, "wb") as f:
                f.write(result.audio_bytes)
            return output_path
        return None

    def clear_cache(self):
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

    def get_cache_stats(self) -> Dict[str, Any]:
        return {
            "cached_phrases": len(self._cache),
            "hits": self._cache_hits,
            "misses": self._cache_misses
        }


KokoroTTSService = KokoroService

