from app.core.celery_app import celery


@celery.task(name="app.tasks.ping")
def ping() -> str:
    return "pong"

