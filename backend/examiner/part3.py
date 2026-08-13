from enum import Enum


class Part3State(Enum):
    INTRODUCTION = "introduction"
    QUESTION = "question"
    LISTENING = "listening"
    EVALUATING = "evaluating"
    FOLLOW_UP = "follow_up"
    COMPLETED = "completed"


PART_3_CONFIG = {
    "name": "Part 3",
    "max_questions": 6,
    "topic_depth_limit": 3,
    "default_topic": "education"
}
