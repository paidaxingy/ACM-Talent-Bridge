from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.member import Member
from app.models.user import User

router = APIRouter(prefix="/me/resume")


@router.post("", status_code=status.HTTP_201_CREATED)
def upload_resume(
    file: Annotated[UploadFile, File()],
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    settings = get_settings()
    member = db.execute(
        select(Member).where(Member.handle == user.username)
    ).scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if file.content_type not in {"application/pdf", "application/msword",
                                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}:
        raise HTTPException(status_code=400, detail="Only PDF/DOC/DOCX files are allowed")

    ext = file.filename.split(".")[-1] if "." in file.filename else ""
    filename = f"member_{member.id}_{hash(file.filename)}_{os.urandom(4).hex()}.{ext}"
    filepath = Path(settings.resumes_dir) / filename
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "wb") as f:
        f.write(file.file.read())

    if member.resume_url:
        old_path = Path(settings.resumes_dir) / member.resume_url.split("/")[-1]
        if old_path.exists():
            old_path.unlink()

    member.resume_filename = file.filename
    member.resume_url = f"/resumes/{filename}"
    db.commit()

    return {"filename": file.filename, "url": member.resume_url}


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    settings = get_settings()
    member = db.execute(
        select(Member).where(Member.handle == user.username)
    ).scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member.resume_url:
        old_path = Path(settings.resumes_dir) / member.resume_url.split("/")[-1]
        if old_path.exists():
            old_path.unlink()

    member.resume_filename = None
    member.resume_url = None
    db.commit()


@router.get("")
def get_resume(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    member = db.execute(
        select(Member).where(Member.handle == user.username)
    ).scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    return {"filename": member.resume_filename, "url": member.resume_url}
