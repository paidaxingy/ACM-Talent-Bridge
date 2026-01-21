from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_admin
from app.models.contest import ContestTeamRegistration
from app.models.member import Member
from app.models.submission import Submission
from app.models.team import Team, TeamMember
from app.models.user import User
from app.schemas.auth import UserOut, UserUpdate

router = APIRouter(prefix="/users")


def _user_to_out(u: User) -> UserOut:
    return UserOut(
        user_id=u.id,
        username=u.username,
        role=u.role,
        is_active=u.is_active,
        created_at=u.created_at,
    )


@router.get("", response_model=list[UserOut])
def list_users(
    role: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    stmt = select(User)
    if role is not None:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)

    users = (
        db.execute(stmt.order_by(User.id.asc()).offset(offset).limit(limit))
        .scalars()
        .all()
    )
    return [_user_to_out(u) for u in users]


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return _user_to_out(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    """删除用户及其关联数据"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 先获取该用户创建的团队列表（在删除成员关系之前）
    teams_created = db.execute(
        select(Team).where(Team.created_by_user_id == user_id)
    ).scalars().all()
    team_ids_created = [t.id for t in teams_created]

    # 删除该用户的团队成员关系
    team_members = db.execute(
        select(TeamMember).where(TeamMember.user_id == user_id)
    ).scalars().all()
    for tm in team_members:
        db.delete(tm)

    # 处理该用户创建的团队（删除成员关系后重新检查）
    for team_id in team_ids_created:
        team = db.get(Team, team_id)
        if not team:
            continue  # 团队可能已被删除
        
        # 检查团队是否还有其他成员（排除当前要删除的用户）
        other_members = db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id != user_id
            )
        ).scalars().all()
        
        # 过滤出用户仍然存在的成员
        valid_members = []
        for tm in other_members:
            member_user = db.get(User, tm.user_id)
            if member_user:
                valid_members.append(tm)
        
        if not valid_members:
            # 没有其他有效成员，先删除团队的竞赛报名记录，再删除团队
            contest_regs = db.execute(
                select(ContestTeamRegistration).where(ContestTeamRegistration.team_id == team_id)
            ).scalars().all()
            for reg in contest_regs:
                db.delete(reg)
            db.delete(team)
        else:
            # 有其他有效成员，将created_by_user_id设为第一个有效成员的user_id
            team.created_by_user_id = valid_members[0].user_id

    # 删除该用户的提交记录的user_id设为NULL（保留提交记录，因为已经有member_id）
    submissions = db.execute(
        select(Submission).where(Submission.user_id == user_id)
    ).scalars().all()
    for submission in submissions:
        submission.user_id = None

    # 删除对应的Member记录（如果handle等于username，注册时自动创建的）
    member = db.execute(
        select(Member).where(Member.handle == user.username)
    ).scalars().first()
    if member:
        db.delete(member)

    # 删除用户
    db.delete(user)
    db.commit()
    return None
