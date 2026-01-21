from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class InterviewSessionCreate(BaseModel):
    member_id: int = Field(ge=1)
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

