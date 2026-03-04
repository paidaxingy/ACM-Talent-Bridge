from __future__ import annotations

import random
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.lab import Lab
from app.models.member import Member
from app.models.pk import PKChallenge, PKMatch, PKParticipant
from app.models.problem import Problem
from app.models.submission import Submission
from app.models.user import User
from app.schemas.pk import PKChallengeCreate, PKChallengeOut, PKMatchCreate, PKMatchFinish, PKMatchOut
from app.services.elo import team_elo_deltas

router = APIRouter(prefix="/pk")


def now_beijing() -> datetime:
    return datetime.now(timezone(timedelta(hours=8))).replace(tzinfo=None)


def _get_match_or_404(match_id: int, db: Session) -> PKMatch:
    match = (
        db.execute(
            select(PKMatch)
            .options(selectinload(PKMatch.participants))
            .where(PKMatch.id == match_id)
        )
        .scalars()
        .first()
    )
    if not match:
        raise HTTPException(status_code=404, detail="PK match not found")
    return match


def _get_challenge_or_404(challenge_id: int, db: Session) -> PKChallenge:
    challenge = (
        db.execute(
            select(PKChallenge)
            .where(PKChallenge.id == challenge_id)
        )
        .scalars()
        .first()
    )
    if not challenge:
        raise HTTPException(status_code=404, detail="PK challenge not found")
    return challenge


def _get_random_problem(db: Session, exclude_member_id: int | None = None) -> Problem | None:
    if exclude_member_id is None:
        problem = db.execute(select(Problem).order_by(func.rand()).limit(1)).scalars().first()
        return problem

    subquery = (
        select(Submission.problem_id)
        .where(Submission.member_id == exclude_member_id)
        .order_by(Submission.created_at.desc())
        .limit(20)
        .subquery()
    )

    problem = (
        db.execute(
            select(Problem)
            .where(Problem.id.not_in(subquery))
            .order_by(func.rand())
            .limit(1)
        )
        .scalars()
        .first()
    )

    if not problem:
        problem = db.execute(select(Problem).order_by(func.rand()).limit(1)).scalars().first()

    return problem


@router.post("/matches", response_model=PKMatchOut, status_code=status.HTTP_201_CREATED)
def create_pk_match(payload: PKMatchCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    lab_id = payload.lab_id
    if lab_id is None:
        lab = db.execute(select(Lab).order_by(Lab.id.asc()).limit(1)).scalars().first()
        if not lab:
            raise HTTPException(status_code=500, detail="Default lab not initialized")
        lab_id = lab.id
    else:
        if not db.get(Lab, lab_id):
            raise HTTPException(status_code=404, detail="Lab not found")

    member_ids = {mid for team in payload.teams for mid in team}
    members = (
        db.execute(select(Member).where(Member.id.in_(member_ids))).scalars().all()
        if member_ids
        else []
    )
    member_map = {m.id: m for m in members}
    if len(member_map) != len(member_ids):
        missing = sorted(member_ids - set(member_map.keys()))
        raise HTTPException(status_code=404, detail={"missing_member_ids": missing})

    for m in members:
        if m.lab_id != lab_id:
            raise HTTPException(status_code=400, detail=f"Member {m.id} does not belong to the same lab")

    match = PKMatch(lab_id=lab_id, title=payload.title, status="pending")
    db.add(match)
    db.flush()

    participants: list[PKParticipant] = []
    for idx, team in enumerate(payload.teams):
        team_no = idx + 1
        for member_id in team:
            member = member_map[member_id]
            participants.append(
                PKParticipant(
                    match_id=match.id,
                    member_id=member_id,
                    team_no=team_no,
                    rating_before=member.rating,
                )
            )

    db.add_all(participants)
    db.commit()

    return _get_match_or_404(match.id, db)


@router.get("/matches", response_model=list[PKMatchOut])
def list_pk_matches(
    lab_id: int | None = Query(default=None, ge=1),
    member_id: int | None = Query(default=None, ge=1),
    status_: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(PKMatch).options(selectinload(PKMatch.participants))
    if lab_id is not None:
        stmt = stmt.where(PKMatch.lab_id == lab_id)
    if status_ is not None:
        stmt = stmt.where(PKMatch.status == status_)
    if member_id is not None:
        stmt = stmt.join(PKParticipant).where(PKParticipant.member_id == member_id)

    matches = (
        db.execute(stmt.order_by(PKMatch.id.desc()).offset(offset).limit(limit))
        .scalars()
        .unique()
        .all()
    )
    return matches


@router.get("/matches/{match_id}", response_model=PKMatchOut)
def get_pk_match(match_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return _get_match_or_404(match_id, db)


@router.post("/matches/{match_id}/finish", response_model=PKMatchOut)
def finish_pk_match(match_id: int, payload: PKMatchFinish, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    match = _get_match_or_404(match_id, db)

    if match.status != "pending":
        raise HTTPException(status_code=400, detail="Match is not pending")

    teams: dict[int, list[PKParticipant]] = {}
    for p in match.participants:
        teams.setdefault(p.team_no, []).append(p)

    if set(teams.keys()) != {1, 2}:
        raise HTTPException(status_code=400, detail="Only 2-team matches are supported")

    if not payload.is_draw and payload.winner_team_no not in (1, 2):
        raise HTTPException(status_code=400, detail="winner_team_no must be 1 or 2")

    score1 = 0.5 if payload.is_draw else (1.0 if payload.winner_team_no == 1 else 0.0)

    team1 = sorted(teams[1], key=lambda p: p.id)
    team2 = sorted(teams[2], key=lambda p: p.id)

    ratings1 = [p.rating_before for p in team1]
    ratings2 = [p.rating_before for p in team2]

    deltas1, deltas2, _exp1 = team_elo_deltas(ratings1, ratings2, score1, k=32)

    for p, d in zip(team1, deltas1):
        p.rating_delta = d
        p.rating_after = p.rating_before + d
        member = db.get(Member, p.member_id)
        if member:
            member.rating = p.rating_after

    for p, d in zip(team2, deltas2):
        p.rating_delta = d
        p.rating_after = p.rating_before + d
        member = db.get(Member, p.member_id)
        if member:
            member.rating = p.rating_after

    match.status = "finished"
    match.is_draw = payload.is_draw
    match.winner_team_no = None if payload.is_draw else payload.winner_team_no
    match.finished_at = now_beijing()

    db.commit()
    return _get_match_or_404(match.id, db)


@router.post("/challenges", response_model=PKChallengeOut, status_code=status.HTTP_201_CREATED)
def create_challenge(payload: PKChallengeCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    challenger = db.execute(select(Member).where(Member.handle == user.username).limit(1)).scalars().first()
    if not challenger:
        raise HTTPException(status_code=404, detail="Member not found")

    challengee = db.get(Member, payload.challengee_member_id)
    if not challengee:
        raise HTTPException(status_code=404, detail="Challengee not found")

    if challenger.id == challengee.id:
        raise HTTPException(status_code=400, detail="Cannot challenge yourself")

    existing = db.execute(
        select(PKChallenge).where(
            PKChallenge.challenger_member_id == challenger.id,
            PKChallenge.challengee_member_id == challengee.id,
            PKChallenge.status.in_(["pending", "accepted"]),
        )
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Active challenge already exists with this user")

    challenge = PKChallenge(
        challenger_member_id=challenger.id,
        challengee_member_id=challengee.id,
        challenger_handle=challenger.handle,
        challengee_handle=challengee.handle,
        status="pending",
    )
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


@router.get("/challenges", response_model=list[PKChallengeOut])
def list_challenges(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    member = db.execute(select(Member).where(Member.handle == user.username).limit(1)).scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    challenges = (
        db.execute(
            select(PKChallenge).where(
                (PKChallenge.challenger_member_id == member.id) | (PKChallenge.challengee_member_id == member.id)
            ).order_by(PKChallenge.id.desc())
        )
        .scalars()
        .all()
    )
    return challenges


@router.get("/challenges/{challenge_id}", response_model=PKChallengeOut)
def get_challenge(challenge_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_challenge_or_404(challenge_id, db)


@router.post("/challenges/{challenge_id}/accept", response_model=PKChallengeOut)
def accept_challenge(challenge_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    challenge = _get_challenge_or_404(challenge_id, db)

    member = db.execute(select(Member).where(Member.handle == user.username).limit(1)).scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if challenge.challengee_member_id != member.id:
        raise HTTPException(status_code=403, detail="Only the challengee can accept")

    if challenge.status != "pending":
        raise HTTPException(status_code=400, detail="Challenge is not pending")

    problem = _get_random_problem(db, member.id)
    if not problem:
        raise HTTPException(status_code=500, detail="No problems available")

    challenge.status = "accepted"
    challenge.problem_id = problem.id
    challenge.started_at = now_beijing()
    db.commit()
    db.refresh(challenge)
    return challenge


@router.post("/challenges/{challenge_id}/reject", response_model=PKChallengeOut)
def reject_challenge(challenge_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    challenge = _get_challenge_or_404(challenge_id, db)

    member = db.execute(select(Member).where(Member.handle == user.username).limit(1)).scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if challenge.challengee_member_id != member.id:
        raise HTTPException(status_code=403, detail="Only the challengee can reject")

    if challenge.status != "pending":
        raise HTTPException(status_code=400, detail="Challenge is not pending")

    challenge.status = "rejected"
    db.commit()
    db.refresh(challenge)
    return challenge


@router.post("/challenges/{challenge_id}/cancel", response_model=PKChallengeOut)
def cancel_challenge(challenge_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    challenge = _get_challenge_or_404(challenge_id, db)

    member = db.execute(select(Member).where(Member.handle == user.username).limit(1)).scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if challenge.challenger_member_id != member.id and challenge.challengee_member_id != member.id:
        raise HTTPException(status_code=403, detail="Not a participant of this challenge")

    if challenge.status not in ["pending", "accepted"]:
        raise HTTPException(status_code=400, detail="Cannot cancel this challenge")

    if challenge.status == "pending":
        if challenge.challenger_member_id != member.id:
            raise HTTPException(status_code=403, detail="Only the challenger can cancel a pending challenge")
        challenge.status = "cancelled"
    else:
        challenge.status = "cancelled"
        challenge.finished_at = now_beijing()
        challenge.is_draw = True
    db.commit()
    db.refresh(challenge)
    return challenge


@router.post("/challenges/{challenge_id}/settle", response_model=PKChallengeOut)
def settle_challenge(challenge_id: int, winner_handle: str | None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    challenge = _get_challenge_or_404(challenge_id, db)

    if challenge.status != "accepted":
        raise HTTPException(status_code=400, detail="Challenge is not active")

    if winner_handle is None:
        challenge.is_draw = True
    else:
        if winner_handle not in [challenge.challenger_handle, challenge.challengee_handle]:
            raise HTTPException(status_code=400, detail="Invalid winner")
        challenge.winner_handle = winner_handle

    challenge.status = "finished"
    challenge.finished_at = now_beijing()

    if not challenge.is_draw and challenge.winner_handle:
        if challenge.winner_handle == challenge.challenger_handle:
            winner = challenge.challenger
            loser = challenge.challengee
        else:
            winner = challenge.challengee
            loser = challenge.challenger

        if winner and loser:
            from app.services.elo import expected_score
            exp = expected_score(winner.rating, loser.rating)
            k = 32
            delta = int(k * (1 - exp))
            winner.rating += delta
            loser.rating -= delta

    db.commit()
    db.refresh(challenge)
    return challenge

