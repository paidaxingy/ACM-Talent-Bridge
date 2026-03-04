from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ContestCreate(BaseModel):
    lab_id: Optional[int] = Field(default=None, ge=1)
    name: str = Field(min_length=1, max_length=128)
    contest_type: str = Field(default="training", max_length=16)
    description: Optional[str] = None
    status: str = Field(default="draft", max_length=16)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None


class ContestUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    contest_type: Optional[str] = Field(default=None, max_length=16)
    description: Optional[str] = None
    status: Optional[str] = Field(default=None, max_length=16)
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None


class ContestProblemAdd(BaseModel):
    problem_id: int = Field(ge=1)
    sort_order: int = Field(default=1, ge=1, le=10_000)
    score: int = Field(default=100, ge=0, le=10_000)


class ContestProblemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contest_id: int
    problem_id: int
    sort_order: int
    score: int


class ContestProblemDetailOut(BaseModel):
    problem_id: int
    problem_letter: str
    problem_title: str
    sort_order: int
    score: int


class ContestRegistrationCreate(BaseModel):
    member_id: Optional[int] = Field(default=None, ge=1)


class ContestRegistrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contest_id: int
    member_id: int
    registered_at: datetime


class ContestTeamRegistrationCreate(BaseModel):
    team_id: int = Field(ge=1)


class ContestTeamRegistrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contest_id: int
    team_id: int
    registered_at: datetime


class TeamMemberBriefOut(BaseModel):
    user_id: int
    username: str


class ContestTeamRegistrationDetailOut(BaseModel):
    team_id: int
    team_name: Optional[str]
    members: list[TeamMemberBriefOut]


class ContestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    name: str
    contest_type: str
    description: Optional[str]
    status: str
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    contest_problems: list[ContestProblemOut] = []

