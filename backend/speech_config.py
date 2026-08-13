class SpeechConfig:
    SAMPLE_RATE = 16000
    FRAME_DURATION_MS = 20
    MIN_SPEECH_MS = 200
    END_SILENCE_MS = 1200
    PRE_ROLL_MS = 300
    MAX_ANSWER_SECONDS = 120


class VADMode:
    PART1 = "part1"
    PART2 = "part2"
    PART3 = "part3"


SETTINGS = {
    "part1": {
        "end_silence_ms": 1200,
        "max_duration": 60
    },
    "part2": {
        "end_silence_ms": 1800,
        "max_duration": 120
    },
    "part3": {
        "end_silence_ms": 1500,
        "max_duration": 90
    }
}
