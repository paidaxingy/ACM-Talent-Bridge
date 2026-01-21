from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from sqlalchemy import select

from app.models.user import User
from app.models.lab import Lab
from app.models.member import Member
from app.schemas.auth import TokenOut, UserCreate, UserOut

router = APIRouter(prefix="/auth")

def _user_to_out(u: User) -> UserOut:
    return UserOut(
        user_id=u.id,
        username=u.username,
        role=u.role,
        is_active=u.is_active,
        created_at=u.created_at,
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """
    MVP: open registration.
    In production, restrict to admins or invite-only.
    """

    user = User(username=payload.username, hashed_password=hash_password(payload.password), role="student")
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # noqa: PERF203
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already exists")
    db.refresh(user)

    # 自动为每个用户创建一条成员档案（handle = username），用于能力画像 / PK / 训练分。
    # 挂到第一个 Lab（init_db 已确保至少存在一个）。
    lab = (
        db.execute(select(Lab).order_by(Lab.id.asc()).limit(1))
        .scalars()
        .first()
    )
    if lab:
        # 同名 handle 已存在时跳过（例如之前手动创建过）。
        existing = (
            db.execute(
                select(Member).where(Member.lab_id == lab.id).where(Member.handle == user.username)
            )
            .scalars()
            .first()
        )
        if not existing:
            m = Member(
                lab_id=lab.id,
                handle=user.username,
                group_name=None,
                tier=1,
                rating=1500,
                is_active=True,
            )
            db.add(m)
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                # 忽略成员创建失败，不影响注册

    return _user_to_out(user)


@router.post("/login", response_model=TokenOut)
async def login(request: Request, db: Session = Depends(get_db)):
    """
    Compatible with both:
    - JSON: {"username": "...", "password": "..."}
    - Form (OAuth2PasswordRequestForm): username=...&password=...
    """

    ctype = (request.headers.get("content-type") or "").lower()
    username = None
    password = None
    if "application/json" in ctype:
        data = await request.json()
        if isinstance(data, dict):
            username = data.get("username")
            password = data.get("password")
    else:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

    if not username or not password:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="username/password required")

    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user.username)
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return _user_to_out(user)

