from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PKMatchCreate(BaseModel):
    lab_id: int | None = Field(default=None, ge=1)
    title: str | None = Field(default=None, max_length=128)

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
    winner_team_no: int | None = Field(default=None, ge=1)
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
    rating_after: int | None
    rating_delta: int | None


class PKMatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lab_id: int
    title: str | None
    status: str
    winner_team_no: int | None
    is_draw: bool
    created_at: datetime
    finished_at: datetime | None
    participants: list[PKParticipantOut]

