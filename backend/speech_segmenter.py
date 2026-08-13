import time
from speech_state import SpeechState


class SpeechSegmenter:

    def __init__(
        self,
        silence_timeout=1.5,
        min_speech_duration=0.3,
        max_answer_duration=60.0
    ):
        self.state = SpeechState.WAITING
        self.silence_timeout = silence_timeout
        self.min_speech_duration = min_speech_duration
        self.max_answer_duration = max_answer_duration
        self.speech_started_at = None
        self.last_speech_at = None

    def process(self, speech_detected: bool):
        now = time.monotonic()

        # Check max duration cap if speech started
        if self.speech_started_at and (now - self.speech_started_at >= self.max_answer_duration):
            self.state = SpeechState.ANSWER_COMPLETE
            return "speech_ended"

        if self.state == SpeechState.WAITING:
            if speech_detected:
                self.state = SpeechState.SPEECH_DETECTED
                self.speech_started_at = now
                self.last_speech_at = now
                return "speech_started"

        elif self.state == SpeechState.SPEECH_DETECTED:
            if speech_detected:
                self.state = SpeechState.SPEAKING
                self.last_speech_at = now
                return "speech_confirmed"
            else:
                self.reset()
                return "speech_cancelled"

        elif self.state == SpeechState.SPEAKING:
            if speech_detected:
                self.last_speech_at = now
                return "speech_continued"
            else:
                self.state = SpeechState.POSSIBLE_END
                return "possible_end"

        elif self.state == SpeechState.POSSIBLE_END:
            if speech_detected:
                self.state = SpeechState.SPEAKING
                self.last_speech_at = now
                return "speech_resumed"

            silence_duration = now - self.last_speech_at
            if silence_duration >= self.silence_timeout:
                self.state = SpeechState.ANSWER_COMPLETE
                return "speech_ended"

        return None

    def reset(self):
        self.state = SpeechState.WAITING
        self.speech_started_at = None
        self.last_speech_at = None
