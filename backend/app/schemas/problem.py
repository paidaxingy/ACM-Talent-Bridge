from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProblemCreate(BaseModel):
    lab_id: int | None = Field(default=None, ge=1)
    title: str = Field(min_length=1, max_length=128)
    statement: str = Field(min_length=1)
    input_desc: str | None = None
    output_desc: str | None = None
    time_limit_ms: int = Field(default=2000, ge=1, le=60_000)
    memory_limit_mb: int = Field(default=256, ge=16, le=8192)


class ProblemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=128)
    statement: str | None = Field(default=None, min_length=1)
    input_desc: str | None = None
    output_desc: str | None = None
    time_limit_ms: int | None = Field(default=None, ge=1, le=60_000)
    memory_limit_mb: int | None = Field(default=None, ge=16, le=8192)


class ProblemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    title: str
    statement: str
    input_desc: str | None
    output_desc: str | None
    time_limit_ms: int
    memory_limit_mb: int
    created_at: datetime
    updated_at: datetime


class TestcaseCreate(BaseModel):
    input_data: str
    expected_output: str
    is_sample: bool = False
    sort_order: int = Field(default=1, ge=1, le=10_000)


class TestcaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    problem_id: int
    input_data: str
    expected_output: str
    is_sample: bool
    sort_order: int
    created_at: datetime

