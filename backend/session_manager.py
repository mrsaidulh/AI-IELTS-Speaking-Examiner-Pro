import uuid
from test_engine import IELTSTestEngine
from answer_buffer import AnswerBuffer
from database import SessionLocal
from models import Student, TestSession


from speech_segmenter import SpeechSegmenter
from rolling_buffer import RollingBuffer


class SessionManager:

    def __init__(self):
        self.sessions = {}
        self.buffers = {}
        self.segmenters = {}
        self.rolling_buffers = {}

    def create_session(self, session_id=None):
        if not session_id:
            session_id = str(uuid.uuid4())
        engine = IELTSTestEngine()
        self.sessions[session_id] = engine
        self.buffers[session_id] = AnswerBuffer()
        self.segmenters[session_id] = SpeechSegmenter()
        self.rolling_buffers[session_id] = RollingBuffer()
        return session_id, engine

    def get_session(self, session_id):
        return self.sessions.get(session_id)

    def get_buffer(self, session_id):
        if session_id not in self.buffers:
            self.buffers[session_id] = AnswerBuffer()
        return self.buffers[session_id]

    def get_segmenter(self, session_id, part="part1"):
        if session_id not in self.segmenters:
            from config import settings
            cfg = settings.PART_CONFIG.get(part, settings.PART_CONFIG["part1"])
            self.segmenters[session_id] = SpeechSegmenter(
                silence_timeout=cfg["silence_timeout"],
                max_answer_duration=cfg["max_answer"]
            )
        return self.segmenters[session_id]

    def get_rolling_buffer(self, session_id):
        if session_id not in self.rolling_buffers:
            self.rolling_buffers[session_id] = RollingBuffer()
        return self.rolling_buffers[session_id]

    def remove_session(self, session_id):
        self.sessions.pop(session_id, None)
        self.buffers.pop(session_id, None)
        self.segmenters.pop(session_id, None)
        self.rolling_buffers.pop(session_id, None)



# DB Helper functions
def create_student(name, email=None):
    db = SessionLocal()
    try:
        student = Student(name=name, email=email)
        db.add(student)
        db.commit()
        db.refresh(student)
        return student
    finally:
        db.close()


def create_test_session(student_id):
    db = SessionLocal()
    try:
        session_id = str(uuid.uuid4())
        test_session = TestSession(
            id=session_id,
            student_id=student_id,
            current_part=1,
            current_question=0,
            status="active"
        )
        db.add(test_session)
        db.commit()
        db.refresh(test_session)
        return test_session
    finally:
        db.close()


def get_test_session(session_id):
    db = SessionLocal()
    try:
        return db.query(TestSession).filter(TestSession.id == session_id).first()
    finally:
        db.close()
