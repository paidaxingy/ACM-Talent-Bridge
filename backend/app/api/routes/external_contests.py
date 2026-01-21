from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.external_contest import ExternalContest
from app.schemas.external_contest import ExternalContestOut
from app.tasks.aggregate_contests import aggregate_contests

router = APIRouter(prefix="/external/contests")


@router.post("/refresh", status_code=status.HTTP_202_ACCEPTED)
def refresh_external_contests():
    """
    Trigger a refresh task (non-blocking).
    """

    async_result = aggregate_contests.delay()
    return {"ok": True, "task_id": async_result.id}


@router.get("", response_model=list[ExternalContestOut])
def list_external_contests(
    source: str | None = Query(default=None),
    upcoming_only: bool = Query(default=True),
    within_days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(ExternalContest)
    if source is not None:
        stmt = stmt.where(ExternalContest.source == source)

    now = datetime.utcnow()
    if upcoming_only:
        stmt = stmt.where(ExternalContest.start_at >= now - timedelta(hours=1))
        stmt = stmt.where(ExternalContest.start_at <= now + timedelta(days=within_days))

    contests = (
        db.execute(stmt.order_by(ExternalContest.start_at.asc()).offset(offset).limit(limit))
        .scalars()
        .all()
    )
    return contests

