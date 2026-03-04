from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_admin
from app.models.lab import Lab
from app.models.member import Member
from app.schemas.member import MemberCreate, MemberOut, MemberUpdate
from app.schemas.profile import MemberAbilityProfileOut
from app.services.ability_profile import resolve_member_profile_view, compute_ability_profile
from app.services.ai_provider import get_ai_provider
from app.services.resume_parser import extract_resume_text
import json
from datetime import datetime

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

    return MemberAbilityProfileOut(**resolve_member_profile_view(db, member))


@router.post("/{member_id}/profile/ai/regenerate", response_model=MemberAbilityProfileOut)
def regenerate_member_ai_profile(
    member_id: int,
    db: Session = Depends(get_db),
    _: "User" = Depends(require_admin),
):
    """
    手动触发指定成员的 AI 能力画像重新生成（管理员专用）。

    - 成功：调用 DeepSeek 生成新画像，覆盖缓存并返回最新画像视图。
    - 失败：记录错误信息，不清空旧缓存，返回 500。
    """
    from app.models.user import User  # local import to avoid circular refs in type hints

    member = db.get(Member, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    provider = get_ai_provider()

    try:
        base = compute_ability_profile(db, member.id)
        summary = base.summary
        resume_text = extract_resume_text(member)
        profile_input = {
            "member_id": summary.member_id,
            "handle": summary.handle,
            "rating": summary.rating,
            "tier": summary.tier,
            "group_name": summary.group_name,
            "pk_total": summary.pk_total,
            "pk_wins": summary.pk_wins,
            "pk_losses": summary.pk_losses,
            "pk_draws": summary.pk_draws,
            "submissions_total": summary.submissions_total,
            "submissions_ac": summary.submissions_ac,
            "contests_registered": summary.contests_registered,
            "interview_avg_score": base.interview_avg_score,
            "rating_trend_last10": base.rating_trend_last10,
            "competitive_strength": base.competitive_strength,
            "consistency": base.consistency,
            "communication": base.communication,
            "problem_solving": base.problem_solving,
            "recommended_directions": base.recommended_directions,
            "improvement_plan": base.improvement_plan,
        }

        ai_result = provider.generate_member_ai_profile(profile_input, resume_text=resume_text)
        cache = {
            "competitive_strength": ai_result.competitive_strength,
            "consistency": ai_result.consistency,
            "communication": ai_result.communication,
            "problem_solving": ai_result.problem_solving,
            "recommended_directions": ai_result.recommended_directions,
            "improvement_plan": ai_result.improvement_plan,
            "persona_summary": ai_result.persona_summary,
        }

        member.ai_profile_cache = json.dumps(cache, ensure_ascii=False)
        member.ai_profile_generated_at = datetime.now()
        member.ai_profile_last_error = None
        db.commit()
    except Exception as e:  # noqa: BLE001
        member.ai_profile_last_error = str(e)[:2000]
        db.commit()
        raise HTTPException(status_code=500, detail=f"AI profile generation failed: {e}")

    # 返回最新画像视图（自动走缓存解析逻辑）
    return MemberAbilityProfileOut(**resolve_member_profile_view(db, member))


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

