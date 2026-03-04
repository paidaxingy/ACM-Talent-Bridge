from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PKMatchCreate(BaseModel):
    lab_id: Optional[int] = Field(default=None, ge=1)
    title: Optional[str] = Field(default=None, max_length=128)

    # Exactly 2 teams for MVP; each team is a list of member_ids
    teams: list[list[int]] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def _validate_teams(self):
        if len(self.teams) != 2:
            raise ValueError("Only 2-team matches are supported for now")
        if any(len(team) == 0 for team in self.teams):
            raise ValueError("Each team must contain at least 1 member")

        flat = [mid for team in self.teams for mid in team]
        if any(mid <= 0 for mid in flat):
            raise ValueError("member_id must be positive")
        if len(flat) != len(set(flat)):
            raise ValueError("Duplicate member_id across teams")
        return self


class PKMatchFinish(BaseModel):
    winner_team_no: Optional[int] = Field(default=None, ge=1)
    is_draw: bool = False

    @model_validator(mode="after")
    def _validate_result(self):
        if self.is_draw:
            if self.winner_team_no is not None:
                raise ValueError("winner_team_no must be null when is_draw=true")
        else:
            if self.winner_team_no is None:
                raise ValueError("winner_team_no is required when is_draw=false")
        return self


class PKParticipantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    member_id: int
    team_no: int
    rating_before: int
    rating_after: Optional[int]
    rating_delta: Optional[int]


class PKMatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    title: Optional[str]
    status: str
    winner_team_no: Optional[int]
    is_draw: bool
    created_at: datetime
    finished_at: Optional[datetime]
    participants: list[PKParticipantOut]


class PKChallengeCreate(BaseModel):
    challengee_member_id: int = Field(..., ge=1)


class PKChallengeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    challenger_member_id: int
    challengee_member_id: int
    challenger_handle: str
    challengee_handle: str
    status: str
    problem_id: Optional[int]
    winner_handle: Optional[str]
    is_draw: bool
    challenger_rating_delta: Optional[int] = None
    challengee_rating_delta: Optional[int] = None
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime


class PKChallengeDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    challenger_member_id: int
    challengee_member_id: int
    challenger_handle: str
    challengee_handle: str
    status: str
    problem_id: Optional[int]
    winner_handle: Optional[str]
    is_draw: bool
    challenger_rating_delta: Optional[int] = None
    challengee_rating_delta: Optional[int] = None
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    created_at: datetime

    challenger: "MemberOut" = Field(exclude=True)
    challengee: "MemberOut" = Field(exclude=True)
    problem: Optional["ProblemOut"] = Field(exclude=True)


class MemberOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    handle: str
    rating: int
    tier: int


class ProblemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str

