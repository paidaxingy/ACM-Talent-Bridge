from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.contest import ContestRegistration
from app.models.member import Member
from app.models.pk import PKChallenge
from app.models.submission import Submission
from app.models.user import User


@dataclass(frozen=True)
class MemberProfileSummary:
    member_id: int
    handle: str
    rating: int
    tier: int
    group_name: str | None

    pk_total: int
    pk_wins: int
    pk_losses: int
    pk_draws: int

    submissions_total: int
    submissions_ac: int

    contests_registered: int

    def to_dict(self) -> dict:
        return asdict(self)


def build_member_profile_summary(db: Session, member_id: int) -> MemberProfileSummary:
    member = db.get(Member, member_id)
    if not member:
        raise ValueError("Member not found")

    # PK stats (only finished 1v1 challenges, based on PKChallenge)
    pk_wins = 0
    pk_losses = 0
    pk_draws = 0
    pk_challenges = (
        db.execute(
            select(PKChallenge)
            .where(PKChallenge.status == "finished")
            .where(
                or_(
                    PKChallenge.challenger_member_id == member_id,
                    PKChallenge.challengee_member_id == member_id,
                )
            )
        )
        .scalars()
        .all()
    )
    handle = member.handle
    for ch in pk_challenges:
        if ch.is_draw:
            pk_draws += 1
        elif ch.winner_handle == handle:
            pk_wins += 1
        else:
            pk_losses += 1
    pk_total = pk_wins + pk_losses + pk_draws

    # Submission stats: 统计该成员的所有提交
    # 优先用 member_id，如果没有则通过 user.username -> member.handle 关联（兼容旧数据）
    submissions_total = int(
        db.execute(
            select(func.count())
            .select_from(Submission)
            .outerjoin(User, User.id == Submission.user_id)
            .where(
                (Submission.member_id == member_id)
                | ((Submission.member_id.is_(None)) & (User.username == handle))
            )
        ).scalar_one()
        or 0
    )
    submissions_ac = int(
        db.execute(
            select(func.count(func.distinct(Submission.problem_id)))
            .select_from(Submission)
            .outerjoin(User, User.id == Submission.user_id)
            .where(
                (Submission.member_id == member_id)
                | ((Submission.member_id.is_(None)) & (User.username == handle))
            )
            .where(Submission.verdict == "AC")
        ).scalar_one()
        or 0
    )

    contests_registered = int(
        db.execute(
            select(func.count())
            .select_from(ContestRegistration)
            .where(ContestRegistration.member_id == member_id)
        ).scalar_one()
    )

    return MemberProfileSummary(
        member_id=member.id,
        handle=member.handle,
        rating=member.rating,
        tier=member.tier,
        group_name=member.group_name,
        pk_total=pk_total,
        pk_wins=pk_wins,
        pk_losses=pk_losses,
        pk_draws=pk_draws,
        submissions_total=submissions_total,
        submissions_ac=submissions_ac,
        contests_registered=contests_registered,
    )

