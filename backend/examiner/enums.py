from enum import Enum


class Part(Enum):
    PART1 = 1
    PART2 = 2
    PART3 = 3


class ExaminerState(Enum):
    IDLE = "idle"
    INTRODUCTION = "introduction"
    PART1 = "part1"
    PART2_INTRO = "part2_intro"
    PART2_PREPARATION = "part2_preparation"
    PART2_SPEAKING = "part2_speaking"
    PART3 = "part3"
    ENDING = "ending"
    PROCESSING = "processing"
    COMPLETED = "completed"


class ConversationState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


class ExamMode(Enum):
    EXAM = "exam"
    PRACTICE = "practice"
