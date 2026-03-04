from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InterviewSessionCreate(BaseModel):
    target_role: str | None = Field(default=None, max_length=64)
    num_questions: int = Field(default=5, ge=1, le=20)


class InterviewQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    sort_order: int
    topic: str | None
    difficulty: str | None
    question: str
    standard_answer: str | None
    created_at: datetime


class InterviewSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: int
    status: str
    target_role: str | None
    num_questions: int
    created_at: datetime
    updated_at: datetime
    questions: list[InterviewQuestionOut] = []


class InterviewAnswerCreate(BaseModel):
    answer: str = Field(min_length=1)


class InterviewAnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int
    attempt: int
    answer: str
    status: str
    score: int | None
    strengths: str | None
    weaknesses: str | None
    suggestions: str | None
    created_at: datetime
    evaluated_at: datetime | None


class InterviewQuestionSummaryOut(BaseModel):
    question_id: int
    sort_order: int
    topic: str | None
    difficulty: str | None
    question: str
    standard_answer: str | None
    latest_attempt: int | None
    latest_score: int | None
    strengths: str | None
    weaknesses: str | None
    suggestions: str | None


class InterviewSessionSummaryOut(BaseModel):
    session_id: int
    total_questions: int
    answered_questions: int
    total_score: float
    questions: list[InterviewQuestionSummaryOut]


class ChatSessionStartIn(BaseModel):
    target_role: str | None = Field(default=None, max_length=64)


class ChatSessionOut(BaseModel):
    id: int
    member_id: int
    status: str
    target_role: str | None
    num_rounds: int
    created_at: datetime
    updated_at: datetime


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    round_no: int
    role: str
    content: str
    difficulty: str | None
    score: int | None
    standard_answer: str | None
    strengths: str | None
    weaknesses: str | None
    suggestions: str | None
    created_at: datetime


class ChatReplyIn(BaseModel):
    answer: str = Field(min_length=1)


class ChatReplyOut(BaseModel):
    session: ChatSessionOut
    candidate_message: ChatMessageOut
    next_question: ChatMessageOut | None


class ChatRoundSummaryOut(BaseModel):
    round_no: int
    question: str
    difficulty: str | None
    answer: str | None
    score: int | None
    standard_answer: str | None
    strengths: str | None
    weaknesses: str | None
    suggestions: str | None


class ChatSessionSummaryOut(BaseModel):
    session_id: int
    status: str
    total_rounds: int
    answered_rounds: int
    total_score: float
    rounds: list[ChatRoundSummaryOut]

