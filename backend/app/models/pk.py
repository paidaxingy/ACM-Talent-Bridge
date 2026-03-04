from __future__ import annotations

from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PKMatch(Base):
    __tablename__ = "pk_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lab_id: Mapped[int] = mapped_column(ForeignKey("labs.id"), index=True)

    title: Mapped[str | None] = mapped_column(String(128), default=None)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/finished/cancelled

    winner_team_no: Mapped[int | None] = mapped_column(Integer, default=None)
    is_draw: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    participants: Mapped[list["PKParticipant"]] = relationship(
        back_populates="match",
        cascade="all, delete-orphan",
    )


class PKParticipant(Base):
    __tablename__ = "pk_participants"
    __table_args__ = (
        UniqueConstraint("match_id", "member_id", name="uq_pk_participant_match_member"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        ForeignKey("pk_matches.id", ondelete="CASCADE"),
        index=True,
    )
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), index=True)

    team_no: Mapped[int] = mapped_column(Integer)  # 1..N

    rating_before: Mapped[int] = mapped_column(Integer)
    rating_after: Mapped[int | None] = mapped_column(Integer, default=None)
    rating_delta: Mapped[int | None] = mapped_column(Integer, default=None)

    match = relationship("PKMatch", back_populates="participants")


class PKChallenge(Base):
    __tablename__ = "pk_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    challenger_member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), index=True)
    challengee_member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), index=True)

    challenger_handle: Mapped[str] = mapped_column(String(64), nullable=False)
    challengee_handle: Mapped[str] = mapped_column(String(64), nullable=False)

    status: Mapped[str] = mapped_column(
        String(16), default="pending"
    )  # pending/accepted/rejected/cancelled/finished

    problem_id: Mapped[int | None] = mapped_column(ForeignKey("problems.id"), index=True, default=None)

    winner_handle: Mapped[str | None] = mapped_column(String(64), default=None)
    is_draw: Mapped[bool] = mapped_column(Boolean, default=False)

    started_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    challenger = relationship("Member", foreign_keys=[challenger_member_id])
    challengee = relationship("Member", foreign_keys=[challengee_member_id])
    problem = relationship("Problem")

