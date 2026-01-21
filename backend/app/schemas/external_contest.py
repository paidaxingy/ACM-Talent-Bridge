from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExternalContestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    external_id: str
    name: str
    url: str
    start_at: datetime
    duration_seconds: int
    contest_type: str | None
    fetched_at: datetime
    updated_at: datetime

