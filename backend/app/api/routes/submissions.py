from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, require_admin
from app.models.contest import Contest
from app.models.member import Member
from app.models.problem import Problem
from app.models.submission import Submission
from app.models.team import Team, TeamMember
from app.models.user import User
from app.schemas.submission import SubmissionCreate, SubmissionOut
from app.tasks.judge import judge_submission

router = APIRouter(prefix="/submissions")


@router.post("", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
def create_submission(
    payload: SubmissionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    problem = db.get(Problem, payload.problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    contest = None
    if payload.contest_id is not None:
        contest = db.get(Contest, payload.contest_id)
        if not contest:
            raise HTTPException(status_code=404, detail="Contest not found")
        # 状态由时间驱动：同步一下，避免用到旧状态
        cn_tz = timezone(timedelta(hours=8))

        def _as_cn_naive(dt: datetime | None) -> datetime | None:
            if dt is None:
                return None
            if dt.tzinfo is None:
                # MySQL DATETIME 无时区，默认按 UTC 存储，再转北京
                return dt.replace(tzinfo=timezone.utc).astimezone(cn_tz).replace(tzinfo=None)
            return dt.astimezone(cn_tz).replace(tzinfo=None)

        now = datetime.now(tz=cn_tz).replace(tzinfo=None)
        start_at = _as_cn_naive(contest.start_at)
        end_at = _as_cn_naive(contest.end_at)

        if contest.status == "draft" and (start_at is None or end_at is None):
            eff = "draft"
        elif end_at is not None and now >= end_at:
            eff = "ended"
        elif start_at is not None and now >= start_at:
            eff = "running"
        else:
            eff = "published"
        if contest.status != eff:
            contest.status = eff
            db.commit()
            db.refresh(contest)

        if user.role != "admin" and contest.status == "draft":
            raise HTTPException(status_code=404, detail="Contest not found")
        if contest.status == "ended":
            raise HTTPException(status_code=403, detail="Contest has ended")
        # 时间驱动：未到开始时间（published）不允许提交
        if user.role != "admin" and contest.status != "running":
            raise HTTPException(status_code=403, detail="Contest is not running")

    if payload.team_id is None:
        team_id = None
    else:
        team = (
            db.execute(select(Team).where(Team.id == payload.team_id))
            .scalars()
            .first()
        )
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        is_member = (
            db.execute(
                select(TeamMember)
                .where(TeamMember.team_id == payload.team_id)
                .where(TeamMember.user_id == user.id)
            )
            .scalars()
            .first()
            is not None
        )
        if not is_member:
            raise HTTPException(status_code=403, detail="Not a team member")
        team_id = payload.team_id

    if team_id is None:
        if payload.contest_id is not None:
            raise HTTPException(status_code=422, detail="team_id required for contest submissions")
    else:
        if payload.contest_id is not None and team_id != payload.team_id:
            raise HTTPException(status_code=400, detail="team_id does not match contest")

    # 自动关联 member_id：根据 user.username 查找对应的 Member（handle = username）
    member_id = None
    if user.username:
        member = (
            db.execute(select(Member).where(Member.handle == user.username).limit(1))
            .scalars()
            .first()
        )
        if member:
            member_id = member.id

    sub = Submission(
        user_id=user.id,
        member_id=member_id,
        team_id=payload.team_id,
        problem_id=payload.problem_id,
        contest_id=payload.contest_id,
        language=payload.language,
        code=payload.code,
        status="pending",
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    async_result = judge_submission.delay(sub.id)
    sub.judge_task_id = async_result.id
    db.commit()
    db.refresh(sub)
    return sub


@router.get("", response_model=list[SubmissionOut])
def list_submissions(
    team_id: int | None = Query(default=None, ge=1),
    problem_id: int | None = Query(default=None, ge=1),
    contest_id: int | None = Query(default=None, ge=1),
    verdict: str | None = Query(default=None),
    status_: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Submission)

    # Security: students can ONLY view their own submissions (even if in the same team).
    if user.role != "admin":
        stmt = stmt.where(Submission.user_id == user.id)

    if team_id is not None:
        stmt = stmt.where(Submission.team_id == team_id)
    if problem_id is not None:
        stmt = stmt.where(Submission.problem_id == problem_id)
    if contest_id is not None:
        stmt = stmt.where(Submission.contest_id == contest_id)
    if verdict is not None:
        stmt = stmt.where(Submission.verdict == verdict)
    if status_ is not None:
        stmt = stmt.where(Submission.status == status_)

    subs = (
        db.execute(stmt.order_by(Submission.id.desc()).offset(offset).limit(limit))
        .scalars()
        .all()
    )

    for sub in subs:
        if sub.member:
            sub.handle = sub.member.handle

    return subs


@router.get("/{submission_id}", response_model=SubmissionOut)
def get_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = db.get(Submission, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    if user.role != "admin" and sub.user_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return sub


@router.post("/{submission_id}/rejudge", response_model=SubmissionOut)
def rejudge(
    submission_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    sub = db.get(Submission, submission_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    sub.status = "pending"
    sub.verdict = None
    sub.time_ms = None
    sub.memory_kb = None
    sub.message = None
    sub.judged_at = None
    db.commit()
    db.refresh(sub)

    async_result = judge_submission.delay(sub.id)
    sub.judge_task_id = async_result.id
    db.commit()
    db.refresh(sub)
    return sub

