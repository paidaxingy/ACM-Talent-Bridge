from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalize_language(lang: str) -> str:
    l = lang.strip().lower()
    if l in {"py", "python", "python3"}:
        return "python3"
    if l in {"cpp", "c++", "cpp17", "cxx"}:
        return "cpp17"
    return l


class SubmissionCreate(BaseModel):
    problem_id: int = Field(ge=1)
    contest_id: int | None = Field(default=None, ge=1)
    team_id: int = Field(ge=1)

    language: str = Field(min_length=1, max_length=16)
    code: str = Field(min_length=1)

    @field_validator("language")
    @classmethod
    def _normalize_lang(cls, v: str) -> str:
        return normalize_language(v)


class SubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    team_id: int | None
    problem_id: int
    contest_id: int | None

    language: str
    code: str
    status: str
    verdict: str | None
    time_ms: int | None
    memory_kb: int | None
    message: str | None
    judge_task_id: str | None

    created_at: datetime
    judged_at: datetime | None

