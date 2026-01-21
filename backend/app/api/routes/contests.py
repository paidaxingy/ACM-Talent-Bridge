from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_db
from app.core.deps import get_current_user, require_admin
from app.models.contest import Contest, ContestProblem, ContestRegistration, ContestTeamRegistration
from app.models.lab import Lab
from app.models.member import Member
from app.models.problem import Problem
from app.models.submission import Submission
from app.models.team import Team, TeamMember
from app.models.user import User
from app.schemas.contest import (
    ContestCreate,
    ContestOut,
    ContestProblemAdd,
    ContestProblemDetailOut,
    ContestProblemOut,
    ContestRegistrationCreate,
    ContestRegistrationOut,
    ContestTeamRegistrationCreate,
    ContestTeamRegistrationDetailOut,
    ContestTeamRegistrationOut,
    TeamMemberBriefOut,
    ContestUpdate,
)

router = APIRouter(prefix="/contests")

def _compute_effective_status(c: Contest, now: datetime) -> str:
    """
    状态完全由时间驱动：
    - 若仍是 draft 且未配置完整时间（start/end 任一缺失） => draft（不对学生可见）
    - now >= end_at => ended
    - now >= start_at => running
    - 否则 => published（未开始/可报名）
    """
    cn_tz = timezone(timedelta(hours=8))

    def _as_cn_naive(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            # MySQL DATETIME 无时区，默认当作存了 UTC，再转北京
            return dt.replace(tzinfo=timezone.utc).astimezone(cn_tz).replace(tzinfo=None)
        return dt.astimezone(cn_tz).replace(tzinfo=None)

    now_n = _as_cn_naive(now) or datetime.now(tz=cn_tz).replace(tzinfo=None)
    start_n = _as_cn_naive(c.start_at)
    end_n = _as_cn_naive(c.end_at)

    if c.status == "draft" and (start_n is None or end_n is None):
        return "draft"
    if end_n is not None and now_n >= end_n:
        return "ended"
    if start_n is not None and now_n >= start_n:
        return "running"
    return "published"


def _sync_status_inplace(contests: list[Contest], db: Session) -> None:
    now = datetime.utcnow()
    changed = False
    for c in contests:
        eff = _compute_effective_status(c, now)
        if c.status != eff:
            c.status = eff
            changed = True
    if changed:
        db.commit()


def _get_contest_or_404(contest_id: int, db: Session) -> Contest:
    contest = (
        db.execute(
            select(Contest)
            .options(selectinload(Contest.contest_problems))
            .where(Contest.id == contest_id)
        )
        .scalars()
        .first()
    )
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    return contest


@router.post("", response_model=ContestOut, status_code=status.HTTP_201_CREATED)
def create_contest(payload: ContestCreate, db: Session = Depends(get_db), _: object = Depends(require_admin)):
    lab_id = payload.lab_id
    if lab_id is None:
        lab = db.execute(select(Lab).order_by(Lab.id.asc()).limit(1)).scalars().first()
        if not lab:
            raise HTTPException(status_code=500, detail="Default lab not initialized")
        lab_id = lab.id
    else:
        if not db.get(Lab, lab_id):
            raise HTTPException(status_code=404, detail="Lab not found")

    contest = Contest(
        lab_id=lab_id,
        name=payload.name,
        contest_type=payload.contest_type,
        description=payload.description,
        # 状态由时间推导：这里先用 draft，后面再同步为 published/running/ended
        status="draft",
        start_at=payload.start_at,
        end_at=payload.end_at,
    )
    # Create 前就同步一次，避免返回给前端时出现“未知”状态
    contest.status = _compute_effective_status(contest, datetime.utcnow())
    db.add(contest)
    db.commit()
    return _get_contest_or_404(contest.id, db)


@router.get("", response_model=list[ContestOut])
def list_contests(
    lab_id: int | None = Query(default=None, ge=1),
    status_: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Contest).options(selectinload(Contest.contest_problems))
    if lab_id is not None:
        stmt = stmt.where(Contest.lab_id == lab_id)
    if user.role != "admin":
        # Student view: hide drafts. (P0: keep it simple)
        stmt = stmt.where(Contest.status != "draft")
    if status_ is not None:
        stmt = stmt.where(Contest.status == status_)

    contests = (
        db.execute(stmt.order_by(Contest.id.desc()).offset(offset).limit(limit))
        .scalars()
        .all()
    )
    _sync_status_inplace(contests, db)
    return contests


@router.get("/{contest_id}", response_model=ContestOut)
def get_contest(
    contest_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contest = _get_contest_or_404(contest_id, db)
    _sync_status_inplace([contest], db)
    if user.role != "admin" and contest.status == "draft":
        raise HTTPException(status_code=404, detail="Contest not found")
    return contest


@router.patch("/{contest_id}", response_model=ContestOut)
def update_contest(
    contest_id: int,
    payload: ContestUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    contest = db.get(Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")

    if payload.name is not None:
        contest.name = payload.name
    if payload.contest_type is not None:
        contest.contest_type = payload.contest_type
    if payload.description is not None:
        contest.description = payload.description
    if payload.start_at is not None:
        contest.start_at = payload.start_at
    if payload.end_at is not None:
        contest.end_at = payload.end_at

    # 状态由时间推导（忽略手动 status）
    contest.status = _compute_effective_status(contest, datetime.utcnow())
    db.commit()
    return _get_contest_or_404(contest_id, db)


@router.delete("/{contest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contest(contest_id: int, db: Session = Depends(get_db), _: object = Depends(require_admin)):
    contest = db.get(Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")

    db.delete(contest)
    db.commit()
    return None


@router.post("/{contest_id}/problems", response_model=ContestProblemOut, status_code=status.HTTP_201_CREATED)
def add_problem_to_contest(
    contest_id: int,
    payload: ContestProblemAdd,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    contest = db.get(Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    _sync_status_inplace([contest], db)

    problem = db.get(Problem, payload.problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    # 产品层已去掉 Lab：允许将任意题目加入竞赛

    cp = ContestProblem(
        contest_id=contest_id,
        problem_id=payload.problem_id,
        sort_order=payload.sort_order,
        score=payload.score,
    )
    db.add(cp)
    try:
        db.commit()
    except IntegrityError:  # noqa: PERF203 (MVP)
        db.rollback()
        raise HTTPException(status_code=409, detail="Problem already exists in contest or sort_order conflicts")

    db.refresh(cp)
    return cp


@router.get("/{contest_id}/problems", response_model=list[ContestProblemOut])
def list_contest_problems(contest_id: int, db: Session = Depends(get_db)):
    if not db.get(Contest, contest_id):
        raise HTTPException(status_code=404, detail="Contest not found")

    cps = (
        db.execute(
            select(ContestProblem)
            .where(ContestProblem.contest_id == contest_id)
            .order_by(ContestProblem.sort_order.asc())
        )
        .scalars()
        .all()
    )
    return cps


@router.get("/{contest_id}/problems/detail", response_model=list[ContestProblemDetailOut])
def list_contest_problems_detail(
    contest_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contest = db.get(Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    if user.role != "admin" and contest.status == "draft":
        raise HTTPException(status_code=404, detail="Contest not found")

    cps = (
        db.execute(
            select(ContestProblem)
            .options(selectinload(ContestProblem.problem))
            .where(ContestProblem.contest_id == contest_id)
            .order_by(ContestProblem.sort_order.asc(), ContestProblem.id.asc())
        )
        .scalars()
        .all()
    )

    out: list[ContestProblemDetailOut] = []
    for idx, cp in enumerate(cps):
        letter = chr(ord("A") + idx)
        title = cp.problem.title if cp.problem else ""
        out.append(
            ContestProblemDetailOut(
                problem_id=cp.problem_id,
                problem_letter=letter,
                problem_title=title,
                sort_order=cp.sort_order,
                score=cp.score,
            )
        )
    return out


@router.post("/{contest_id}/register", response_model=ContestTeamRegistrationOut, status_code=status.HTTP_201_CREATED)
def register_contest(
    contest_id: int,
    payload: ContestTeamRegistrationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contest = db.get(Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    _sync_status_inplace([contest], db)
    if user.role != "admin" and contest.status == "draft":
        raise HTTPException(status_code=404, detail="Contest not found")
    # 时间驱动：已结束不可报名
    if contest.status == "ended":
        raise HTTPException(status_code=403, detail="Contest has ended")

    team = (
        db.execute(
            select(Team)
            .options(selectinload(Team.members))
            .where(Team.id == payload.team_id)
        )
        .scalars()
        .first()
    )
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if not any(tm.user_id == user.id for tm in (team.members or [])):
        raise HTTPException(status_code=403, detail="Not a team member")

    # 产品层已去掉 Lab：不再绑定/校验 team.lab_id

    reg = ContestTeamRegistration(contest_id=contest_id, team_id=payload.team_id)
    db.add(reg)
    try:
        db.commit()
    except IntegrityError:  # noqa: PERF203 (MVP)
        db.rollback()
        raise HTTPException(status_code=409, detail="Team already registered")

    db.refresh(reg)
    return reg


@router.get("/{contest_id}/registrations", response_model=list[ContestTeamRegistrationDetailOut])
def list_registrations(
    contest_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not db.get(Contest, contest_id):
        raise HTTPException(status_code=404, detail="Contest not found")

    stmt = (
        select(ContestTeamRegistration)
        .options(selectinload(ContestTeamRegistration.team).selectinload(Team.members))
        .where(ContestTeamRegistration.contest_id == contest_id)
        .order_by(ContestTeamRegistration.id.asc())
    )
    regs = db.execute(stmt).scalars().all()

    # Student can only see registrations of teams they are in (P0 minimal).
    if user.role != "admin":
        allowed_team_ids = {
            r.team_id
            for r in regs
            if r.team and any(tm.user_id == user.id for tm in (r.team.members or []))
        }
        regs = [r for r in regs if r.team_id in allowed_team_ids]

    # hydrate usernames in one query
    team_member_user_ids = sorted(
        {
            tm.user_id
            for r in regs
            for tm in ((r.team.members if r.team else None) or [])
        }
    )
    users = (
        db.execute(select(User).where(User.id.in_(team_member_user_ids))).scalars().all()
        if team_member_user_ids
        else []
    )
    user_map = {u.id: u for u in users}

    out: list[ContestTeamRegistrationDetailOut] = []
    for r in regs:
        team = r.team
        members = (team.members if team else []) or []
        out.append(
            ContestTeamRegistrationDetailOut(
                team_id=r.team_id,
                team_name=team.name if team else None,
                members=[
                    TeamMemberBriefOut(user_id=tm.user_id, username=(user_map.get(tm.user_id).username if user_map.get(tm.user_id) else ""))
                    for tm in members
                ],
            )
        )
    return out


@router.get("/{contest_id}/scoreboard")
def get_scoreboard(
    contest_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    contest = db.get(Contest, contest_id)
    if not contest:
        raise HTTPException(status_code=404, detail="Contest not found")
    _sync_status_inplace([contest], db)
    if user.role != "admin" and contest.status == "draft":
        raise HTTPException(status_code=404, detail="Contest not found")

    # contest problems (ordered)
    cps = (
        db.execute(
            select(ContestProblem)
            .where(ContestProblem.contest_id == contest_id)
            .order_by(ContestProblem.sort_order.asc())
        )
        .scalars()
        .all()
    )
    problem_ids = [cp.problem_id for cp in cps]

    # gather all done submissions for this contest (team-based)
    subs = (
        db.execute(
            select(Submission)
            .where(Submission.contest_id == contest_id)
            .where(Submission.status == "done")
            .where(Submission.team_id.is_not(None))
            .order_by(Submission.created_at.asc(), Submission.id.asc())
        )
        .scalars()
        .all()
    )

    # team info (include registered teams even if no submissions)
    regs = (
        db.execute(select(ContestTeamRegistration).where(ContestTeamRegistration.contest_id == contest_id))
        .scalars()
        .all()
    )
    team_ids = sorted({int(s.team_id) for s in subs if s.team_id is not None} | {r.team_id for r in regs})

    teams = (
        db.execute(
            select(Team)
            .options(selectinload(Team.members))
            .where(Team.id.in_(team_ids))
        )
        .scalars()
        .all()
        if team_ids
        else []
    )
    team_map = {t.id: t for t in teams}

    member_user_ids = sorted(
        {tm.user_id for t in teams for tm in (t.members or [])}
    )
    users = (
        db.execute(select(User).where(User.id.in_(member_user_ids))).scalars().all()
        if member_user_ids
        else []
    )
    user_map = {u.id: u for u in users}

    start_at = contest.start_at or contest.created_at

    def minutes_since_start(ts):
        return max(0, int((ts - start_at).total_seconds() // 60))

    # ACM-style aggregation
    # state[team_id][problem_id] = {"solved": bool, "wrong": int, "time": int|None}
    state: dict[int, dict[int, dict[str, int | bool | None]]] = {}
    for tid in team_ids:
        state[tid] = {}
        for pid in problem_ids:
            state[tid][pid] = {"solved": False, "wrong": 0, "time": None}

    for s in subs:
        if s.team_id is None:
            continue
        tid = int(s.team_id)
        if tid not in state:
            continue
        if s.problem_id not in state[tid]:
            continue

        cell = state[tid][s.problem_id]
        if cell["solved"]:
            continue

        if s.verdict == "AC":
            cell["solved"] = True
            cell["time"] = minutes_since_start(s.created_at)
        else:
            cell["wrong"] = int(cell["wrong"] or 0) + 1

    rows = []
    for tid in team_ids:
        solved = 0
        penalty = 0
        problems = []
        for pid in problem_ids:
            cell = state[tid][pid]
            solved_flag = bool(cell["solved"])
            wrong = int(cell["wrong"] or 0)
            t = cell["time"]
            if solved_flag:
                solved += 1
                penalty += int(t or 0) + 20 * wrong
            problems.append(
                {
                    "problem_id": pid,
                    "solved": solved_flag,
                    "wrong": wrong,
                    "time_minutes": t,
                }
            )

        team = team_map.get(tid)
        members = (team.members if team else []) or []
        rows.append(
            {
                "team_id": tid,
                "team_name": team.name if team else None,
                "members": [
                    {"user_id": tm.user_id, "username": (user_map.get(tm.user_id).username if user_map.get(tm.user_id) else "")}
                    for tm in members
                ],
                "solved": solved,
                "penalty_minutes": penalty,
                "problems": problems,
            }
        )

    rows.sort(key=lambda r: (-r["solved"], r["penalty_minutes"], r["team_id"]))

    return {
        "contest_id": contest_id,
        "start_at": start_at,
        "problems": problem_ids,
        "rows": rows,
    }

