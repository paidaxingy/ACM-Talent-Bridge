from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    member_id: Mapped[int | None] = mapped_column(ForeignKey("members.id"), index=True, default=None)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), index=True, default=None)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True, default=None)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    contest_id: Mapped[int | None] = mapped_column(ForeignKey("contests.id"), index=True, default=None)

    language: Mapped[str] = mapped_column(String(16))
    code: Mapped[str] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/judging/done
    verdict: Mapped[str | None] = mapped_column(String(8), default=None)  # AC/WA/CE/RE/TLE/SE
    time_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    memory_kb: Mapped[int | None] = mapped_column(Integer, default=None)
    message: Mapped[str | None] = mapped_column(Text, default=None)

    judge_task_id: Mapped[str | None] = mapped_column(String(64), default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    judged_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    member = relationship("Member")
    team = relationship("Team")
    user = relationship("User")
    problem = relationship("Problem")
    contest = relationship("Contest")

