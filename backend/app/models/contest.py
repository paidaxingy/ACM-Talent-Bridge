from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Contest(Base):
    __tablename__ = "contests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lab_id: Mapped[int] = mapped_column(ForeignKey("labs.id"), index=True)

    name: Mapped[str] = mapped_column(String(128), index=True)
    contest_type: Mapped[str] = mapped_column(String(16), default="training")  # training/selection/mock
    description: Mapped[str | None] = mapped_column(Text, default=None)

    status: Mapped[str] = mapped_column(String(16), default="draft")  # draft/registration/running/finished
    start_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    end_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    created_at: Mapped[datetime] = mapped_column(
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

    contest_problems: Mapped[list["ContestProblem"]] = relationship(
        back_populates="contest",
        cascade="all, delete-orphan",
    )
    registrations: Mapped[list["ContestRegistration"]] = relationship(
        back_populates="contest",
        cascade="all, delete-orphan",
    )


class ContestProblem(Base):
    __tablename__ = "contest_problems"
    __table_args__ = (
        UniqueConstraint("contest_id", "problem_id", name="uq_contest_problem"),
        UniqueConstraint("contest_id", "sort_order", name="uq_contest_sort_order"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contest_id: Mapped[int] = mapped_column(
        ForeignKey("contests.id", ondelete="CASCADE"),
        index=True,
    )
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)

    sort_order: Mapped[int] = mapped_column(Integer, default=1)
    score: Mapped[int] = mapped_column(Integer, default=100)

    contest = relationship("Contest", back_populates="contest_problems")
    problem = relationship("Problem")


class ContestRegistration(Base):
    __tablename__ = "contest_registrations"
    __table_args__ = (
        UniqueConstraint("contest_id", "member_id", name="uq_contest_member"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contest_id: Mapped[int] = mapped_column(
        ForeignKey("contests.id", ondelete="CASCADE"),
        index=True,
    )
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"), index=True)

    registered_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    contest = relationship("Contest", back_populates="registrations")
    member = relationship("Member")


class ContestTeamRegistration(Base):
    __tablename__ = "contest_team_registrations"
    __table_args__ = (UniqueConstraint("contest_id", "team_id", name="uq_contest_team"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contest_id: Mapped[int] = mapped_column(
        ForeignKey("contests.id", ondelete="CASCADE"),
        index=True,
    )
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)

    registered_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    contest = relationship("Contest")
    team = relationship("Team")

