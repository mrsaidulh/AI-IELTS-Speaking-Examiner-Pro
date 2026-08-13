from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey
)
from database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    name = Column(
        String(100),
        nullable=False
    )
    email = Column(
        String(150),
        nullable=True
    )

class TestSession(Base):
    __tablename__ = "test_sessions"

    id = Column(
        String(100),
        primary_key=True,
        index=True
    )
    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False
    )
    current_part = Column(
        Integer,
        default=1
    )
    current_question = Column(
        Integer,
        default=0
    )
    current_state = Column(
        String(30),
        default="idle"
    )
    timer_started_at = Column(
        DateTime,
        nullable=True
    )
    status = Column(
        String(30),
        default="active"
    )
    started_at = Column(
        DateTime,
        default=datetime.utcnow
    )
    completed_at = Column(
        DateTime,
        nullable=True
    )

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    session_id = Column(
        String(100),
        ForeignKey("test_sessions.id"),
        nullable=False
    )
    part = Column(
        Integer,
        nullable=False
    )
    question = Column(
        Text,
        nullable=False
    )
    answer = Column(
        Text,
        nullable=False
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

class Answer(Base):
    __tablename__ = "answers"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    session_id = Column(
        String(100),
        ForeignKey("test_sessions.id"),
        nullable=False
    )
    part = Column(
        Integer,
        nullable=False
    )
    question = Column(
        Text,
        nullable=False
    )
    transcript = Column(
        Text,
        nullable=False
    )
    audio_path = Column(
        String(500),
        nullable=True
    )
    duration = Column(
        Float,
        nullable=True
    )
    audio_metrics = Column(
        Text,
        nullable=True
    )

class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    session_id = Column(
        String(100),
        ForeignKey("test_sessions.id"),
        nullable=False
    )
    fluency = Column(
        Float,
        nullable=True
    )
    lexical = Column(
        Float,
        nullable=True
    )
    grammar = Column(
        Float,
        nullable=True
    )
    pronunciation = Column(
        Float,
        nullable=True
    )
    overall = Column(
        Float,
        nullable=True
    )
    fluency_band = Column(
        Float,
        nullable=True
    )
    lexical_band = Column(
        Float,
        nullable=True
    )
    grammar_band = Column(
        Float,
        nullable=True
    )
    pronunciation_band = Column(
        Float,
        nullable=True
    )
    overall_band = Column(
        Float,
        nullable=True
    )
    feedback = Column(
        Text,
        nullable=True
    )
    report = Column(
        Text,
        nullable=True
    )
