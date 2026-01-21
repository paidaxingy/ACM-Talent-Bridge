from __future__ import annotations

from dataclasses import asdict, dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.contest import ContestRegistration
from app.models.member import Member
from app.models.pk import PKMatch, PKParticipant
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

    # PK stats (only finished matches)
    pk_rows = (
        db.execute(
            select(PKParticipant.team_no, PKMatch.winner_team_no, PKMatch.is_draw)
            .join(PKMatch, PKMatch.id == PKParticipant.match_id)
            .where(PKParticipant.member_id == member_id)
            .where(PKMatch.status == "finished")
        )
        .all()
    )
    pk_total = len(pk_rows)
    pk_wins = 0
    pk_losses = 0
    pk_draws = 0
    for team_no, winner_team_no, is_draw in pk_rows:
        if is_draw:
            pk_draws += 1
        elif winner_team_no == team_no:
            pk_wins += 1
        else:
            pk_losses += 1

    # Submission stats: 统计该成员的所有提交
    # 优先用 member_id，如果没有则通过 user.username -> member.handle 关联（兼容旧数据）
    handle = member.handle
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

