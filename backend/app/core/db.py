from __future__ import annotations

import time
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


def _create_engine():
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


engine = _create_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def wait_for_db(timeout_s: int = 30) -> None:
    """
    Docker compose `depends_on` does NOT wait for DB readiness.
    This makes API startup more robust by retrying for a short period.
    """

    deadline = time.time() + timeout_s
    last_err: Exception | None = None

    while time.time() < deadline:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as e:  # noqa: BLE001 (MVP)
            last_err = e
            time.sleep(1)

    raise RuntimeError("Database is not ready") from last_err


def init_db() -> None:
    """
    Ensure DB is reachable and create tables for current metadata.

    MVP uses `create_all`; later we will migrate to Alembic migrations.
    """

    wait_for_db()
    from app.models.base import Base

    # Import models so they register tables into Base.metadata
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Lightweight compatibility migration for MVP environments still using create_all.
    # create_all won't ALTER existing tables, so we patch required interview columns here.
    try:
        inspector = inspect(engine)
        columns = {c["name"] for c in inspector.get_columns("interview_questions")}
        if "standard_answer" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE interview_questions ADD COLUMN standard_answer TEXT NULL"))
    except Exception:
        # Best-effort only; should not block startup in constrained environments.
        pass

    # MVP convenience: ensure there is at least one default Lab so admin pages
    # (Problems/Contests) don't require users to manually create and remember a lab_id.
    try:
        from app.models.lab import Lab

        with SessionLocal() as db:
            exists = db.query(Lab).first()
            if not exists:
                db.add(Lab(name="ACM实验室", description="默认实验室（自动创建）"))
                db.commit()
    except Exception:
        # Avoid blocking startup due to a best-effort convenience step.
        pass
