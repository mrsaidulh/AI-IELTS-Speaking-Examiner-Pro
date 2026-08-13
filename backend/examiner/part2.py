from enum import Enum


class Part2State(Enum):
    INTRODUCTION = "introduction"
    CUE_CARD = "cue_card"
    PREPARATION = "preparation"
    READY = "ready"
    LONG_TURN = "long_turn"
    FINISHING = "finishing"
    COMPLETED = "completed"


PART_2_CONFIG = {
    "name": "Part 2",
    "preparation_time": 60,
    "long_turn_time": 120,
    "silence_threshold": 3.0,
}
