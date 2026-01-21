from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_db
from app.models.lab import Lab
from app.models.member import Member
from app.models.pk import PKMatch, PKParticipant
from app.schemas.pk import PKMatchCreate, PKMatchFinish, PKMatchOut
from app.services.elo import team_elo_deltas

router = APIRouter(prefix="/pk")


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


@router.post("/matches", response_model=PKMatchOut, status_code=status.HTTP_201_CREATED)
def create_pk_match(payload: PKMatchCreate, db: Session = Depends(get_db)):
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
    db.flush()  # assign match.id

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

    # Reload with participants for response serialization
    return _get_match_or_404(match.id, db)


@router.get("/matches", response_model=list[PKMatchOut])
def list_pk_matches(
    lab_id: int | None = Query(default=None, ge=1),
    member_id: int | None = Query(default=None, ge=1),
    status_: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
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
def get_pk_match(match_id: int, db: Session = Depends(get_db)):
    return _get_match_or_404(match_id, db)


@router.post("/matches/{match_id}/finish", response_model=PKMatchOut)
def finish_pk_match(match_id: int, payload: PKMatchFinish, db: Session = Depends(get_db)):
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

    # Apply updates
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
    match.finished_at = datetime.utcnow()

    db.commit()
    return _get_match_or_404(match.id, db)

