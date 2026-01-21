from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from app.core.celery_app import celery
from app.core.config import get_settings
from app.core.db import SessionLocal
from app.models.problem import Problem
from app.models.problem import Testcase
from app.models.submission import Submission
from app.schemas.submission import normalize_language
from app.services.judge_docker import judge_in_docker
from app.services.judge_local import judge_python3


@celery.task(name="app.tasks.judge_submission")
def judge_submission(submission_id: int) -> dict:
    """
    Judge a submission asynchronously.

    MVP:
    - Supports Python3 local judging (inside worker container/host)
    - Docker sandbox mode will be added as an alternative runner
    """

    settings = get_settings()

    with SessionLocal() as db:
        sub = db.get(Submission, submission_id)
        if not sub:
            return {"ok": False, "error": "submission_not_found"}

        sub.status = "judging"
        db.commit()

        lang = normalize_language(sub.language)
        problem = db.get(Problem, sub.problem_id)
        time_limit_ms = (problem.time_limit_ms if problem else None) or settings.judge_time_limit_ms
        memory_limit_mb = (problem.memory_limit_mb if problem else None) or settings.judge_memory_limit_mb
        tcs = (
            db.execute(
                select(Testcase)
                .where(Testcase.problem_id == sub.problem_id)
                .order_by(Testcase.sort_order.asc())
            )
            .scalars()
            .all()
        )

        if settings.judge_enable_docker:
            result = judge_in_docker(
                code=sub.code,
                language=lang,
                testcases=tcs,
                time_limit_ms=time_limit_ms,
                memory_limit_mb=memory_limit_mb,
                settings=settings,
            )
        else:
            if lang != "python3":
                sub.status = "done"
                sub.verdict = "CE"
                sub.message = f"Language not supported in MVP runner: {lang}"
                sub.judged_at = datetime.utcnow()
                db.commit()
                return {"ok": True, "verdict": sub.verdict}

            result = judge_python3(sub.code, tcs, time_limit_ms=time_limit_ms)

        sub.status = "done"
        sub.verdict = result.verdict
        sub.time_ms = result.time_ms
        sub.memory_kb = result.memory_kb
        sub.message = result.message
        sub.judged_at = datetime.utcnow()
        db.commit()
        return {"ok": True, "verdict": sub.verdict}

