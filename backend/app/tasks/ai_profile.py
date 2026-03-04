from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import select

from app.core.celery_app import celery
from app.core.db import SessionLocal
from app.models.member import Member
from app.services.ability_profile import compute_ability_profile
from app.services.ai_provider import get_ai_provider
from app.services.resume_parser import extract_resume_text


@celery.task(name="app.tasks.generate_daily_ai_profiles")
def generate_daily_ai_profiles() -> dict:
    """
    Generate AI profile cache once per day.

    - Success: overwrite cache + generated timestamp, clear last error
    - Failure: keep previous cache unchanged, only update last error
    """
    provider = get_ai_provider()
    ok = 0
    failed = 0
    errors: dict[int, str] = {}

    with SessionLocal() as db:
        members = (
            db.execute(select(Member).where(Member.is_active.is_(True)).order_by(Member.id.asc()))
            .scalars()
            .all()
        )

        for member in members:
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
                ok += 1
            except Exception as e:  # noqa: BLE001
                member.ai_profile_last_error = str(e)[:2000]
                db.commit()
                failed += 1
                errors[member.id] = str(e)

    return {"ok": True, "updated": ok, "failed": failed, "errors": errors}
