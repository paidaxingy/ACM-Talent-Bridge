from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.team import Team, TeamMember
from app.models.user import User
from app.schemas.team import TeamCreate, TeamMemberOut, TeamOut

router = APIRouter(prefix="/teams")

TEAM_MAX_MEMBERS = 3


def _team_to_out(team: Team) -> TeamOut:
    return TeamOut(
        team_id=team.id,
        team_name=team.name,
        team_members=[
            TeamMemberOut(
                user_id=tm.user_id,
                username=tm.user.username if tm.user else "",
                joined_at=tm.joined_at,
            )
            for tm in (team.members or [])
        ],
    )


def _get_team_or_404(team_id: int, db: Session) -> Team:
    team = (
        db.execute(
            select(Team)
            .options(selectinload(Team.members).selectinload(TeamMember.user))
            .where(Team.id == team_id)
        )
        .scalars()
        .first()
    )
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.post("", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    team = Team(name=payload.team_name, created_by_user_id=user.id)
    db.add(team)
    db.flush()  # allocate team.id

    db.add(TeamMember(team_id=team.id, user_id=user.id))
    db.commit()
    team = _get_team_or_404(team.id, db)
    return _team_to_out(team)


@router.post("/{team_id}/join", response_model=TeamOut)
def join_team(
    team_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    team = _get_team_or_404(team_id, db)

    if any(tm.user_id == user.id for tm in team.members):
        raise HTTPException(status_code=409, detail="Already in team")
    if len(team.members) >= TEAM_MAX_MEMBERS:
        raise HTTPException(status_code=409, detail="Team is full")

    db.add(TeamMember(team_id=team_id, user_id=user.id))
    try:
        db.commit()
    except IntegrityError:  # noqa: PERF203 (MVP)
        db.rollback()
        raise HTTPException(status_code=409, detail="Already in team")

    team = _get_team_or_404(team_id, db)
    return _team_to_out(team)


@router.post("/{team_id}/leave", response_model=TeamOut)
def leave_team(
    team_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    team = _get_team_or_404(team_id, db)

    me = next((tm for tm in team.members if tm.user_id == user.id), None)
    if not me:
        raise HTTPException(status_code=409, detail="Not in team")

    db.delete(me)
    db.commit()

    team = _get_team_or_404(team_id, db)
    if len(team.members) == 0:
        db.delete(team)
        db.commit()
        raise HTTPException(status_code=404, detail="Team not found")

    return _team_to_out(team)
