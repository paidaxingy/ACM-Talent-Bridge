from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.interview import InterviewAnswer, InterviewQuestion, InterviewSession
from app.models.member import Member
from app.models.pk import PKChallenge
from app.services.member_profile import MemberProfileSummary, build_member_profile_summary


@dataclass(frozen=True)
class AbilityProfile:
    summary: MemberProfileSummary

    interview_avg_score: float | None
    rating_trend_last10: int

    # Dimension scores: 0-100
    competitive_strength: int
    consistency: int
    communication: int
    problem_solving: int

    recommended_directions: list[dict]
    improvement_plan: list[str]

    def to_dict(self) -> dict:
        d = asdict(self)
        # nested dataclass -> dict
        d["summary"] = self.summary.to_dict()
        return d


def _clamp(v: float, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, int(round(v))))


def compute_ability_profile(db: Session, member_id: int) -> AbilityProfile:
    summary = build_member_profile_summary(db, member_id)

    # Interview average score
    interview_avg_score = db.execute(
        select(func.avg(InterviewAnswer.score))
        .select_from(InterviewAnswer)
        .join(InterviewQuestion, InterviewQuestion.id == InterviewAnswer.question_id)
        .join(InterviewSession, InterviewSession.id == InterviewQuestion.session_id)
        .where(InterviewSession.member_id == member_id)
        .where(InterviewAnswer.status == "done")
        .where(InterviewAnswer.score.is_not(None))
    ).scalar_one()
    interview_avg = float(interview_avg_score) if interview_avg_score is not None else None

    # Rating trend (last 10 finished PKChallenge deltas for this member)
    recent_challenges = (
        db.execute(
            select(PKChallenge)
            .where(
                (PKChallenge.challenger_member_id == member_id)
                | (PKChallenge.challengee_member_id == member_id)
            )
            .where(PKChallenge.status == "finished")
            .order_by(PKChallenge.finished_at.desc(), PKChallenge.id.desc())
            .limit(10)
        )
        .scalars()
        .all()
    )
    deltas: list[int] = []
    for ch in recent_challenges:
        if ch.challenger_member_id == member_id:
            delta = ch.challenger_rating_delta
        else:
            delta = ch.challengee_rating_delta
        if delta is not None:
            deltas.append(int(delta))
    rating_trend_last10 = int(sum(deltas))

    # Dimension heuristics
    # Competitive strength: map rating 1200..2400 -> 20..95
    competitive_strength = _clamp(20 + (summary.rating - 1200) * (75 / 1200))

    # Consistency: based on PK volume + winrate; encourage more matches
    winrate = (summary.pk_wins / summary.pk_total) if summary.pk_total > 0 else 0.0
    volume_bonus = min(1.0, summary.pk_total / 30.0)
    consistency = _clamp(40 + 50 * winrate * volume_bonus)

    # Communication: from interview average (if absent, conservative)
    communication = _clamp(interview_avg if interview_avg is not None else 55)

    # Problem solving: from AC rate + rating
    ac_rate = (summary.submissions_ac / summary.submissions_total) if summary.submissions_total > 0 else 0.0
    problem_solving = _clamp(30 + 50 * ac_rate + 0.02 * (summary.rating - 1500))

    # Career directions (rule-based)
    dirs: list[dict] = []
    if summary.rating >= 2000 and communication >= 75:
        dirs.append({"direction": "算法/竞赛向研发", "reason": "高竞技分 + 面试表达能力较好，适合算法岗/竞赛向团队。"})
    if summary.rating >= 1700 and problem_solving >= 70:
        dirs.append({"direction": "后端开发（需要较强算法基础）", "reason": "算法基础不错，继续补齐工程能力即可。"})
    if communication >= 80 and (summary.rating < 1700):
        dirs.append({"direction": "后端/全栈（工程实践优先）", "reason": "表达与结构化能力较好，建议通过项目与工程实践提升竞争力。"})
    if not dirs:
        dirs.append({"direction": "算法基础提升路线", "reason": "建议先提升刷题覆盖面与稳定性，再冲刺更高阶岗位。"})

    plan: list[str] = []
    if summary.submissions_total < 50:
        plan.append("提高训练量：每周至少 20~30 题（含复盘），形成题型覆盖。")
    if summary.pk_total < 10:
        plan.append("增加对抗次数：参与更多 PK/训练赛，积累压力环境下的稳定性。")
    if communication < 70:
        plan.append("面试表达训练：每题按“思路→复杂度→边界→示例”组织回答，做 5 次模拟面试。")
    if rating_trend_last10 < 0:
        plan.append("复盘最近对抗：总结失分原因（读题/实现/思维盲区），针对性补弱。")
    if not plan:
        plan.append("保持节奏：每周固定训练 + 定期复盘 + 阶段性模拟面试。")

    return AbilityProfile(
        summary=summary,
        interview_avg_score=interview_avg,
        rating_trend_last10=rating_trend_last10,
        competitive_strength=competitive_strength,
        consistency=consistency,
        communication=communication,
        problem_solving=problem_solving,
        recommended_directions=dirs,
        improvement_plan=plan,
    )


def resolve_member_profile_view(db: Session, member: Member) -> dict:
    """
    Build profile view payload for API.
    Priority:
    1) valid AI cache in member table
    2) rule-based computed profile
    """
    p = compute_ability_profile(db, member.id)
    s = p.summary

    payload = {
        "member_id": s.member_id,
        "handle": s.handle,
        "rating": s.rating,
        "tier": s.tier,
        "group_name": s.group_name,
        "pk_total": s.pk_total,
        "pk_wins": s.pk_wins,
        "pk_losses": s.pk_losses,
        "pk_draws": s.pk_draws,
        "submissions_total": s.submissions_total,
        "submissions_ac": s.submissions_ac,
        "contests_registered": s.contests_registered,
        "interview_avg_score": p.interview_avg_score,
        "rating_trend_last10": p.rating_trend_last10,
        "competitive_strength": p.competitive_strength,
        "consistency": p.consistency,
        "communication": p.communication,
        "problem_solving": p.problem_solving,
        "recommended_directions": p.recommended_directions,
        "improvement_plan": p.improvement_plan,
        "persona_summary": None,
        "ai_profile_generated_at": None,
        "ai_profile_source": "rule",
    }

    if not member.ai_profile_cache:
        return payload

    try:
        obj = json.loads(member.ai_profile_cache)
        if not isinstance(obj, dict):
            return payload

        def _score(name: str, default: int) -> int:
            raw = obj.get(name, default)
            return max(0, min(100, int(raw)))

        directions = obj.get("recommended_directions")
        if not isinstance(directions, list):
            directions = payload["recommended_directions"]

        plan = obj.get("improvement_plan")
        if not isinstance(plan, list):
            plan = payload["improvement_plan"]

        payload.update(
            {
                "competitive_strength": _score("competitive_strength", payload["competitive_strength"]),
                "consistency": _score("consistency", payload["consistency"]),
                "communication": _score("communication", payload["communication"]),
                "problem_solving": _score("problem_solving", payload["problem_solving"]),
                "recommended_directions": directions,
                "improvement_plan": [str(x) for x in plan if str(x).strip()],
                "persona_summary": str(obj.get("persona_summary", "")).strip() or None,
                "ai_profile_generated_at": member.ai_profile_generated_at,
                "ai_profile_source": "ai_cache",
            }
        )
        return payload
    except Exception:  # noqa: BLE001
        return payload

