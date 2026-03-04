from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery = Celery(
    "acm_talent_bridge",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    enable_utc=False,
    timezone="Asia/Shanghai",
    task_track_started=True,
    task_always_eager=settings.celery_always_eager,
    task_eager_propagates=settings.celery_eager_propagates,
)

# Periodic tasks (Celery Beat)
celery.conf.beat_schedule = {
    "aggregate-contests-daily-cst-0005": {
        "task": "app.tasks.aggregate_contests",
        "schedule": crontab(minute=5, hour=0),
    }
}

celery.autodiscover_tasks(["app"])

