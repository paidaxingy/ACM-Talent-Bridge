from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Member(Base):
    __tablename__ = "members"
    __table_args__ = (
        UniqueConstraint("lab_id", "handle", name="uq_members_lab_handle"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lab_id: Mapped[int] = mapped_column(ForeignKey("labs.id"), index=True)

    # Competition handle / nickname (unique within a lab)
    handle: Mapped[str] = mapped_column(String(64))

    # Profile
    real_name: Mapped[str | None] = mapped_column(String(64), default=None)
    email: Mapped[str | None] = mapped_column(String(128), default=None)

    # Training management
    group_name: Mapped[str | None] = mapped_column(String(64), default=None)
    tier: Mapped[int] = mapped_column(Integer, default=1)

    # Rating (Elo-like)
    rating: Mapped[int] = mapped_column(Integer, default=1500)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Resume
    resume_filename: Mapped[str | None] = mapped_column(String(256), default=None)
    resume_url: Mapped[str | None] = mapped_column(String(512), default=None)

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

    lab = relationship("Lab", back_populates="members")

