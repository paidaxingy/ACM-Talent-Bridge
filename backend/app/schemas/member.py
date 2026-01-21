from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MemberCreate(BaseModel):
    lab_id: int | None = Field(default=None, ge=1)
    handle: str = Field(min_length=1, max_length=64)

    real_name: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=128)

    group_name: str | None = Field(default=None, max_length=64)
    tier: int = Field(default=1, ge=1, le=10)

    rating: int = Field(default=1500, ge=0, le=4000)
    is_active: bool = True


class MemberUpdate(BaseModel):
    lab_id: int | None = Field(default=None, ge=1)
    handle: str | None = Field(default=None, min_length=1, max_length=64)

    real_name: str | None = Field(default=None, max_length=64)
    email: str | None = Field(default=None, max_length=128)

    group_name: str | None = Field(default=None, max_length=64)
    tier: int | None = Field(default=None, ge=1, le=10)

    rating: int | None = Field(default=None, ge=0, le=4000)
    is_active: bool | None = None


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    handle: str
    real_name: str | None
    email: str | None
    group_name: str | None
    tier: int
    rating: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

