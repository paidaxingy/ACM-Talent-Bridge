from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.team import Team, TeamMember
from app.models.user import User
from app.models.member import Member
from app.models.contest import ContestTeamRegistration, ContestRegistration
from app.schemas.profile import MemberAbilityProfileOut
from app.schemas.team import TeamMemberOut, TeamOut
from app.services.ability_profile import resolve_member_profile_view

router = APIRouter(prefix="/me")


@router.get("/profile", response_model=MemberAbilityProfileOut)
def my_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    基于当前登录用户的用户名，查找同名成员（handle = username），并返回能力画像。
    前置条件：管理员在"成员管理"中为该用户名创建了对应的 member 记录。
    """
    member = (
      db.execute(
          select(Member).where(Member.handle == user.username)
      )
      .scalars()
      .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found for current user")

    return MemberAbilityProfileOut(**resolve_member_profile_view(db, member))


@router.get("/teams", response_model=list[TeamOut])
def my_teams(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    teams = (
        db.execute(
            select(Team)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .options(selectinload(Team.members).selectinload(TeamMember.user))
            .where(TeamMember.user_id == user.id)
            .order_by(Team.id.desc())
        )
        .scalars()
        .all()
    )

    return [
        TeamOut(
            team_id=t.id,
            team_name=t.name,
            team_members=[
                TeamMemberOut(
                    user_id=tm.user_id,
                    username=tm.user.username if tm.user else "",
                    joined_at=tm.joined_at,
                )
                for tm in (t.members or [])
            ],
        )
        for t in teams
    ]


@router.get("/contests/{contest_id}/active_team")
def my_active_team_for_contest(
    contest_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    查询当前用户在某场比赛中的报名信息（队伍或个人）。
    """
    team_reg = (
        db.execute(
            select(ContestTeamRegistration)
            .join(Team, Team.id == ContestTeamRegistration.team_id)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .where(ContestTeamRegistration.contest_id == contest_id)
            .where(TeamMember.user_id == user.id)
        )
        .scalars()
        .first()
    )
    if team_reg:
        team = db.get(Team, team_reg.team_id)
        return {"team_id": team.id if team else team_reg.team_id, "team_name": team.name if team else None}

    member = db.execute(select(Member).where(Member.handle == user.username).limit(1)).scalars().first()
    if member:
        individual_reg = db.execute(
            select(ContestRegistration)
            .where(ContestRegistration.contest_id == contest_id)
            .where(ContestRegistration.member_id == member.id)
        ).scalars().first()
        if individual_reg:
            return {"team_id": -member.id, "team_name": "个人参赛"}

    return {"team_id": None, "team_name": None}

