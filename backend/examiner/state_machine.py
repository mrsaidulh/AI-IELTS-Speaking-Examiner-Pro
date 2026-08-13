from enum import Enum


class Part1State(Enum):
    INTRODUCTION = "introduction"
    TOPIC_START = "topic_start"
    ASKING = "asking"
    LISTENING = "listening"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
