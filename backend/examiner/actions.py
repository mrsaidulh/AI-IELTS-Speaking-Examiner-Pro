from enum import Enum


class ExaminerAction(str, Enum):
    """
    Strict Enum representing allowed actions performed by the IELTS Examiner.
    Inherits from (str, Enum) for direct string equality checks and Pydantic validation.
    """
    ASK_NEXT = "ASK_NEXT"
    REPEAT = "REPEAT"
    CLARIFY = "CLARIFY"
    MOVE_PART = "MOVE_PART"
    START_SPEAKING = "START_SPEAKING"
    END_PART = "END_PART"
    END_TEST = "END_TEST"

    @classmethod
    def _missing_(cls, value: object):
        if isinstance(value, str):
            value_upper = value.upper()
            for member in cls:
                if member.value == value_upper:
                    return member
        return None
