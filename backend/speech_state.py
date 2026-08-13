from enum import Enum


class SpeechState(Enum):
    WAITING = "waiting"
    SPEECH_DETECTED = "speech_detected"
    SPEAKING = "speaking"
    POSSIBLE_END = "possible_end"
    ANSWER_COMPLETE = "answer_complete"
