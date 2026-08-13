from enum import Enum
from typing import Any, Dict, Optional


class WebSocketState(str, Enum):
    """
    Candidate real-time UI state model for WebSocket communication.
    """
    IDLE = "IDLE"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    READY = "READY"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    THINKING = "THINKING"
    EXAMINER_SPEAKING = "EXAMINER_SPEAKING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class WebSocketEventType(str, Enum):
    """
    Standardized event types for Client <-> Server WebSocket messaging.
    """
    # Client -> Server
    SESSION_START = "session_start"
    SPEECH_START = "speech_start"
    SPEECH_END = "speech_end"
    AUDIO_START = "audio_start"
    AUDIO_CHUNK = "audio_chunk"
    AUDIO_END = "audio_end"
    PING = "ping"

    # Server -> Client
    SESSION_READY = "session_ready"
    STATE = "state"
    LISTENING_STARTED = "listening.started"
    SPEECH_STARTED = "speech.started"
    SPEECH_POSSIBLE_END = "speech.possible_end"
    SPEECH_RESUMED = "speech.resumed"
    SPEECH_ENDED = "speech.ended"
    TRANSCRIPT = "transcript"
    TRANSCRIPT_PARTIAL = "transcript.partial"
    TRANSCRIPT_FINAL = "transcript.final"
    EXAMINER_THINKING = "examiner_thinking"
    EXAMINER_RESPONSE = "examiner_response"
    EXAMINER_TEXT = "examiner_text"
    EXAMINER_AUDIO = "examiner_audio"
    EXAMINER_FINISHED = "examiner.finished"
    TIMER = "timer"
    ERROR = "error"
    SESSION_COMPLETE = "session_complete"
    PONG = "pong"



def format_ws_event(event_type: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Formats standardized WebSocket event payloads following {"type": ..., "data": {...}}.
    """
    return {
        "type": event_type,
        "data": data or {}
    }


def format_state_event(state: WebSocketState, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Helper to construct a server state update event.
    """
    payload = {"state": state.value}
    if details:
        payload.update(details)
    return format_ws_event(WebSocketEventType.STATE.value, payload)


def format_error_event(message: str, code: str = "ERROR") -> Dict[str, Any]:
    """
    Helper to construct a server error event.
    """
    return format_ws_event(WebSocketEventType.ERROR.value, {
        "message": message,
        "code": code
    })
