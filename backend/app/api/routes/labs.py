from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.lab import Lab
from app.schemas.lab import LabCreate, LabOut, LabUpdate

router = APIRouter(prefix="/labs")


@router.post("", response_model=LabOut, status_code=status.HTTP_201_CREATED)
def create_lab(payload: LabCreate, db: Session = Depends(get_db)):
    lab = Lab(name=payload.name, description=payload.description)
    db.add(lab)
    try:
        db.commit()
    except IntegrityError:  # noqa: PERF203 (MVP)
        db.rollback()
        raise HTTPException(status_code=409, detail="Lab name already exists")
    db.refresh(lab)
    return lab


@router.get("", response_model=list[LabOut])
def list_labs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    labs = (
        db.execute(select(Lab).order_by(Lab.id.asc()).offset(offset).limit(limit))
        .scalars()
        .all()
    )
    return labs


@router.get("/{lab_id}", response_model=LabOut)
def get_lab(lab_id: int, db: Session = Depends(get_db)):
    lab = db.get(Lab, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    return lab


@router.patch("/{lab_id}", response_model=LabOut)
def update_lab(lab_id: int, payload: LabUpdate, db: Session = Depends(get_db)):
    lab = db.get(Lab, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    if payload.name is not None:
        lab.name = payload.name
    if payload.description is not None:
        lab.description = payload.description

    try:
        db.commit()
    except IntegrityError:  # noqa: PERF203 (MVP)
        db.rollback()
        raise HTTPException(status_code=409, detail="Lab name already exists")

    db.refresh(lab)
    return lab


@router.delete("/{lab_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lab(lab_id: int, db: Session = Depends(get_db)):
    lab = db.get(Lab, lab_id)
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    db.delete(lab)
    db.commit()
    return None

