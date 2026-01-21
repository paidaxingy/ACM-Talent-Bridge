from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TeamCreate(BaseModel):
    team_name: str | None = Field(default=None, max_length=128)


class TeamMemberOut(BaseModel):
    user_id: int
    username: str
    joined_at: datetime


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: int
    team_name: str | None
    team_members: list[TeamMemberOut]

