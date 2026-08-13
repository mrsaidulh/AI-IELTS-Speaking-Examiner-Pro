import os
import sys
import io
import wave
import struct
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from speech.schema import Transcript, TranscriptSegment
from speech.whisper_service import WhisperService
from audio.buffer import AudioBuffer
from audio.vad import VADSegmenter, EnergyVAD
from websocket.events import handle_websocket_message, ws_manager


def create_dummy_wav_bytes(duration_sec: float = 1.0, sample_rate: int = 16000) -> bytes:
    """
    Generates valid 16kHz Mono 16-bit PCM WAV bytes for testing.
    """
    sample_count = int(sample_rate * duration_sec)
    samples = [int(1000 * (i % 2 - 0.5)) for i in range(sample_count)]
    pcm_bytes = struct.pack(f"<{sample_count}h", *samples)

    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    return wav_io.getvalue()


def test_transcript_schema_validation():
    print("--- Test 1: Pydantic Transcript & TranscriptSegment Schema Validation ---")

    seg1 = TranscriptSegment(start=0.0, end=2.5, text="I am from Mymensingh")
    seg2 = TranscriptSegment(start=2.5, end=5.0, text="and I really enjoy living there because it is peaceful.")
    
    transcript = Transcript(
        text="I am from Mymensingh and I really enjoy living there because it is peaceful.",
        language="en",
        segments=[seg1, seg2],
        language_probability=0.99
    )

    assert transcript.text.startswith("I am from Mymensingh")
    assert len(transcript.segments) == 2
    assert transcript.segments[0].start == 0.0
    assert transcript.segments[0].end == 2.5
    assert transcript.language == "en"

    serialized = transcript.model_dump()
    assert "segments" in serialized
    assert serialized["segments"][0]["text"] == "I am from Mymensingh"
    print("✓ Transcript & TranscriptSegment Pydantic schema validation & serialization verified.")


def test_whisper_service_transcribe_raw_bytes():
    print("\n--- Test 2: WhisperService Transcription from Raw WAV Bytes ---")

    whisper = WhisperService(model_size="small", device="cpu")
    wav_bytes = create_dummy_wav_bytes(duration_sec=1.5)

    result = whisper.transcribe(wav_bytes, language="en", task="transcribe")

    assert isinstance(result, Transcript)
    assert len(result.text) > 0
    assert len(result.segments) > 0
    assert result.language == "en"
    print(f"✓ WhisperService transcribed raw WAV bytes successfully (Text: '{result.text}').")


class MockWebSocket:
    def __init__(self):
        self.sent_events = []

    async def accept(self):
        pass

    async def send_text(self, text: str):
        self.sent_events.append(text)

    async def send_bytes(self, data: bytes):
        pass


async def test_websocket_audio_buffer_vad_whisper_pipeline():
    print("\n--- Test 3: AudioBuffer + VAD + Whisper End-to-End Event Pipeline ---")

    mock_ws = MockWebSocket()
    session_id = "test_lesson45_pipeline"
    await ws_manager.connect(session_id, mock_ws)

    # 1. audio_start
    await handle_websocket_message(session_id, mock_ws, {"type": "audio_start", "data": {}})
    print("✓ Pipeline initialized (audio_start).")

    # 2. Append audio chunk (1 second PCM)
    sample_count = 16000
    samples = [1500 if (i % 100 < 50) else -1500 for i in range(sample_count)]
    pcm_bytes = struct.pack(f"<{sample_count}h", *samples)
    
    ws_manager.append_audio_chunk(session_id, pcm_bytes)
    audio_buf = ws_manager.audio_buffers[session_id]
    assert audio_buf.get_duration_seconds() == 1.0
    print("✓ 1.0s audio chunk appended and processed through VAD.")

    # 3. audio_end -> triggers WhisperService transcription
    res_end = await handle_websocket_message(session_id, mock_ws, {"type": "audio_end", "data": {}})
    
    assert res_end["data"]["state"] in ("PROCESSING", "EXAMINER_SPEAKING")
    assert "transcript" in res_end["data"]
    assert len(res_end["data"]["transcript"]) > 0
    print(f"✓ 'audio_end' event produced structured transcript: '{res_end['data']['transcript']}'.")

    ws_manager.disconnect(session_id)


def main():
    print("===============================================================")
    print("   Running Lesson 45 Unit & Integration Test Suite            ")
    print("===============================================================")
    test_transcript_schema_validation()
    test_whisper_service_transcribe_raw_bytes()
    asyncio.run(test_websocket_audio_buffer_vad_whisper_pipeline())
    print("\n✓ ALL LESSON 45 TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
