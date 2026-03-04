from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), index=True)

    status: Mapped[str] = mapped_column(String(16), default="generating")  # generating/ready/finished/failed
    target_role: Mapped[str | None] = mapped_column(String(64), default=None)
    num_questions: Mapped[int] = mapped_column(Integer, default=5)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    questions: Mapped[list["InterviewQuestion"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    chat_messages: Mapped[list["InterviewChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    __table_args__ = (
        UniqueConstraint("session_id", "sort_order", name="uq_interview_session_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        index=True,
    )

    sort_order: Mapped[int] = mapped_column(Integer, default=1)
    topic: Mapped[str | None] = mapped_column(String(64), default=None)
    difficulty: Mapped[str | None] = mapped_column(String(16), default=None)  # easy/medium/hard
    question: Mapped[str] = mapped_column(Text)
    standard_answer: Mapped[str | None] = mapped_column(Text, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    session = relationship("InterviewSession", back_populates="questions")
    answers: Mapped[list["InterviewAnswer"]] = relationship(
        back_populates="question_ref",
        cascade="all, delete-orphan",
    )


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"
    __table_args__ = (
        UniqueConstraint("question_id", "attempt", name="uq_interview_answer_attempt"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        index=True,
    )

    attempt: Mapped[int] = mapped_column(Integer, default=1)

    answer: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/evaluating/done/failed

    score: Mapped[int | None] = mapped_column(Integer, default=None)  # 0-100
    strengths: Mapped[str | None] = mapped_column(Text, default=None)
    weaknesses: Mapped[str | None] = mapped_column(Text, default=None)
    suggestions: Mapped[str | None] = mapped_column(Text, default=None)
    raw: Mapped[str | None] = mapped_column(Text, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    question_ref = relationship("InterviewQuestion", back_populates="answers")


class InterviewChatMessage(Base):
    __tablename__ = "interview_chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("interview_sessions.id", ondelete="CASCADE"),
        index=True,
    )
    round_no: Mapped[int] = mapped_column(Integer, default=1)
    role: Mapped[str] = mapped_column(String(16))  # interviewer/candidate
    content: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str | None] = mapped_column(String(16), default=None)  # easy/medium/hard

    # Candidate-side evaluated fields
    score: Mapped[int | None] = mapped_column(Integer, default=None)
    standard_answer: Mapped[str | None] = mapped_column(Text, default=None)
    strengths: Mapped[str | None] = mapped_column(Text, default=None)
    weaknesses: Mapped[str | None] = mapped_column(Text, default=None)
    suggestions: Mapped[str | None] = mapped_column(Text, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    session = relationship("InterviewSession", back_populates="chat_messages")

