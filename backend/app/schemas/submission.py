from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def normalize_language(lang: str) -> str:
    l = lang.strip().lower()
    if l in {"py", "python", "python3"}:
        return "python3"
    if l in {"cpp", "c++", "cpp17", "cxx"}:
        return "cpp17"
    return l


class SubmissionCreate(BaseModel):
    problem_id: int = Field(ge=1)
    contest_id: Optional[int] = Field(default=None, ge=1)
    team_id: Optional[int] = Field(default=None, ge=1)

    language: str = Field(min_length=1, max_length=16)
    code: str = Field(min_length=1)

    @field_validator("language")
    @classmethod
    def _normalize_lang(cls, v: str) -> str:
        return normalize_language(v)


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    member_id: Optional[int]
    user_id: Optional[int]
    team_id: Optional[int]
    problem_id: int
    contest_id: Optional[int]

    language: str
    code: str
    status: str
    verdict: Optional[str]
    time_ms: Optional[int]
    memory_kb: Optional[int]
    message: Optional[str]
    judge_task_id: Optional[str]

    handle: Optional[str] = None

    created_at: datetime
    judged_at: Optional[datetime]

