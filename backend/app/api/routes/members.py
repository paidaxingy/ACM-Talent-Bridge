from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.lab import Lab
from app.models.member import Member
from app.schemas.member import MemberCreate, MemberOut, MemberUpdate
from app.schemas.profile import MemberAbilityProfileOut
from app.services.ability_profile import compute_ability_profile

router = APIRouter(prefix="/members")


@router.post("", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def create_member(payload: MemberCreate, db: Session = Depends(get_db)):
    lab_id = payload.lab_id
    if lab_id is None:
        lab = db.execute(select(Lab).order_by(Lab.id.asc()).limit(1)).scalars().first()
        if not lab:
            raise HTTPException(status_code=500, detail="Default lab not initialized")
        lab_id = lab.id
    else:
        if not db.get(Lab, lab_id):
            raise HTTPException(status_code=404, detail="Lab not found")

    member = Member(
        lab_id=lab_id,
        handle=payload.handle,
        real_name=payload.real_name,
        email=payload.email,
        group_name=payload.group_name,
        tier=payload.tier,
        rating=payload.rating,
        is_active=payload.is_active,
    )
    db.add(member)
    try:
        db.commit()
    except IntegrityError:  # noqa: PERF203 (MVP)
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Member handle already exists in this lab",
        )
    db.refresh(member)
    return member


@router.get("", response_model=list[MemberOut])
def list_members(
    lab_id: int | None = Query(default=None, ge=1),
    group_name: str | None = Query(default=None),
    tier: int | None = Query(default=None, ge=1, le=10),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Member)
    if lab_id is not None:
        stmt = stmt.where(Member.lab_id == lab_id)
    if group_name is not None:
        stmt = stmt.where(Member.group_name == group_name)
    if tier is not None:
        stmt = stmt.where(Member.tier == tier)

    members = (
        db.execute(
            stmt.order_by(Member.rating.desc(), Member.id.asc()).offset(offset).limit(limit)
        )
        .scalars()
        .all()
    )
    return members


@router.get("/{member_id}", response_model=MemberOut)
def get_member(member_id: int, db: Session = Depends(get_db)):
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.get("/{member_id}/profile", response_model=MemberAbilityProfileOut)
def get_member_profile(member_id: int, db: Session = Depends(get_db)):
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    p = compute_ability_profile(db, member_id)
    s = p.summary
    return MemberAbilityProfileOut(
        member_id=s.member_id,
        handle=s.handle,
        rating=s.rating,
        tier=s.tier,
        group_name=s.group_name,
        pk_total=s.pk_total,
        pk_wins=s.pk_wins,
        pk_losses=s.pk_losses,
        pk_draws=s.pk_draws,
        submissions_total=s.submissions_total,
        submissions_ac=s.submissions_ac,
        contests_registered=s.contests_registered,
        interview_avg_score=p.interview_avg_score,
        rating_trend_last10=p.rating_trend_last10,
        competitive_strength=p.competitive_strength,
        consistency=p.consistency,
        communication=p.communication,
        problem_solving=p.problem_solving,
        recommended_directions=p.recommended_directions,
        improvement_plan=p.improvement_plan,
    )


@router.patch("/{member_id}", response_model=MemberOut)
def update_member(member_id: int, payload: MemberUpdate, db: Session = Depends(get_db)):
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if payload.lab_id is not None:
        # 仍保留该字段用于内部数据归属；如传入则做合法性校验
        if not db.get(Lab, payload.lab_id):
            raise HTTPException(status_code=404, detail="Lab not found")
        member.lab_id = payload.lab_id

    if payload.handle is not None:
        member.handle = payload.handle
    if payload.real_name is not None:
        member.real_name = payload.real_name
    if payload.email is not None:
        member.email = payload.email
    if payload.group_name is not None:
        member.group_name = payload.group_name
    if payload.tier is not None:
        member.tier = payload.tier
    if payload.rating is not None:
        member.rating = payload.rating
    if payload.is_active is not None:
        member.is_active = payload.is_active

    try:
        db.commit()
    except IntegrityError:  # noqa: PERF203 (MVP)
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Member handle already exists in this lab",
        )

    db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(member_id: int, db: Session = Depends(get_db)):
    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    db.delete(member)
    db.commit()
    return None

