from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.celery_app import celery
from app.core.db import SessionLocal
from app.models.interview import InterviewAnswer, InterviewQuestion, InterviewSession
from app.services.ai_provider import get_ai_provider
from app.services.member_profile import build_member_profile_summary


@celery.task(name="app.tasks.generate_interview_questions")
def generate_interview_questions(session_id: int) -> dict:
    provider = get_ai_provider()

    with SessionLocal() as db:
        session = (
            db.execute(
                select(InterviewSession)
                .options(selectinload(InterviewSession.questions))
                .where(InterviewSession.id == session_id)
            )
            .scalars()
            .first()
        )
        if not session:
            return {"ok": False, "error": "session_not_found"}

        try:
            profile = build_member_profile_summary(db, session.member_id).to_dict()
            qs = provider.generate_questions(
                profile,
                num_questions=session.num_questions,
                target_role=session.target_role,
            )

            # Ensure idempotency: if questions already exist, do not duplicate
            if session.questions:
                session.status = "ready"
                db.commit()
                return {"ok": True, "skipped": True}

            for i, q in enumerate(qs[: session.num_questions], start=1):
                db.add(
                    InterviewQuestion(
                        session_id=session.id,
                        sort_order=i,
                        topic=q.topic,
                        difficulty=q.difficulty,
                        question=q.question,
                    )
                )

            session.status = "ready"
            db.commit()
            return {"ok": True, "count": len(qs)}
        except Exception as e:  # noqa: BLE001
            session.status = "failed"
            db.commit()
            return {"ok": False, "error": str(e)}


@celery.task(name="app.tasks.evaluate_interview_answer")
def evaluate_interview_answer(answer_id: int) -> dict:
    provider = get_ai_provider()

    with SessionLocal() as db:
        ans = (
            db.execute(
                select(InterviewAnswer)
                .options(selectinload(InterviewAnswer.question_ref))
                .where(InterviewAnswer.id == answer_id)
            )
            .scalars()
            .first()
        )
        if not ans:
            return {"ok": False, "error": "answer_not_found"}

        q = ans.question_ref
        if not q:
            ans.status = "failed"
            db.commit()
            return {"ok": False, "error": "question_not_found"}

        session = db.get(InterviewSession, q.session_id)
        if not session:
            ans.status = "failed"
            db.commit()
            return {"ok": False, "error": "session_not_found"}

        try:
            ans.status = "evaluating"
            db.commit()

            profile = build_member_profile_summary(db, session.member_id).to_dict()
            eva = provider.evaluate_answer(profile, question=q.question, answer=ans.answer)

            ans.score = max(0, min(100, int(eva.score)))
            ans.strengths = eva.strengths
            ans.weaknesses = eva.weaknesses
            ans.suggestions = eva.suggestions
            ans.raw = eva.raw
            ans.status = "done"
            ans.evaluated_at = datetime.utcnow()
            db.commit()
            return {"ok": True, "score": ans.score}
        except Exception as e:  # noqa: BLE001
            ans.status = "failed"
            db.commit()
            return {"ok": False, "error": str(e)}

