from enum import Enum


class IELTSPart(Enum):
    PART_1 = "part1"
    PART_2 = "part2"
    PART_3 = "part3"


class SessionState(Enum):
    NOT_STARTED = "not_started"
    INTRODUCTION = "introduction"
    PART_1 = "part1"
    PART_2 = "part2"
    PART_3 = "part3"
    FINISHED = "finished"


class IELTSSession:

    def __init__(self, candidate_name="Candidate", session_id="demo-session"):
        self.session_id = session_id
        self.candidate_name = candidate_name
        self.state = SessionState.NOT_STARTED
        self.question_number = 0
        self.current_question = None
        self.answers = []
        self.topics_covered = []

    def record_answer(self, transcript, duration):
        answer_data = {
            "question_number": self.question_number,
            "question": self.current_question,
            "answer": transcript,
            "duration": round(duration, 2)
        }
        self.answers.append(answer_data)
        return answer_data

    def set_question(self, question_text):
        self.question_number += 1
        self.current_question = question_text


class ExaminerSession(IELTSSession):
    """
    Alias class for ExaminerSession used across ExaminerController.
    """
    pass

