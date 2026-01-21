from __future__ import annotations

from pydantic import BaseModel, Field


class MemberAbilityProfileOut(BaseModel):
    member_id: int
    handle: str
    rating: int
    tier: int
    group_name: str | None

    pk_total: int
    pk_wins: int
    pk_losses: int
    pk_draws: int

    submissions_total: int
    submissions_ac: int
    contests_registered: int

    interview_avg_score: float | None
    rating_trend_last10: int

    competitive_strength: int = Field(ge=0, le=100)
    consistency: int = Field(ge=0, le=100)
    communication: int = Field(ge=0, le=100)
    problem_solving: int = Field(ge=0, le=100)

    recommended_directions: list[dict]
    improvement_plan: list[str]

