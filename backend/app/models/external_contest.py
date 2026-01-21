from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ExternalContest(Base):
    __tablename__ = "external_contests"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_external_source_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # e.g. codeforces / atcoder / nowcoder
    source: Mapped[str] = mapped_column(String(16), index=True)
    # platform-native identifier: CF contestId, AtCoder contest slug, etc.
    external_id: Mapped[str] = mapped_column(String(64))

    name: Mapped[str] = mapped_column(String(256), index=True)
    url: Mapped[str] = mapped_column(String(512))

    start_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)

    contest_type: Mapped[str | None] = mapped_column(String(64), default=None)
    raw: Mapped[str | None] = mapped_column(Text, default=None)

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

