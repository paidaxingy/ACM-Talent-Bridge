from __future__ import annotations

from sqlalchemy import select

from app.core.celery_app import celery
from app.core.db import SessionLocal
from app.models.external_contest import ExternalContest
from app.services.contest_aggregator import default_sources


@celery.task(name="app.tasks.aggregate_contests")
def aggregate_contests() -> dict:
    """
    Fetch contest schedules from external platforms and upsert into DB.
    """

    sources = default_sources()
    upserted = 0
    errors: dict[str, str] = {}

    with SessionLocal() as db:
        for src in sources:
            try:
                items = src.fetch()
            except Exception as e:  # noqa: BLE001 (best-effort aggregation)
                errors[src.source_name] = str(e)
                continue

            for item in items:
                existing = (
                    db.execute(
                        select(ExternalContest)
                        .where(ExternalContest.source == item.source)
                        .where(ExternalContest.external_id == item.external_id)
                    )
                    .scalars()
                    .first()
                )
                if existing:
                    existing.name = item.name
                    existing.url = item.url
                    existing.start_at = item.start_at
                    existing.duration_seconds = item.duration_seconds
                    existing.contest_type = item.contest_type
                    existing.raw = item.raw
                else:
                    db.add(
                        ExternalContest(
                            source=item.source,
                            external_id=item.external_id,
                            name=item.name,
                            url=item.url,
                            start_at=item.start_at,
                            duration_seconds=item.duration_seconds,
                            contest_type=item.contest_type,
                            raw=item.raw,
                        )
                    )
                upserted += 1

        db.commit()

    return {"ok": True, "upserted": upserted, "errors": errors}

