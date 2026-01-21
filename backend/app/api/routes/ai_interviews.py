from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_db
from app.models.interview import InterviewAnswer, InterviewQuestion, InterviewSession
from app.models.member import Member
from app.schemas.interview import (
    InterviewAnswerCreate,
    InterviewAnswerOut,
    InterviewQuestionOut,
    InterviewSessionCreate,
    InterviewSessionOut,
)
from app.tasks.ai_interview import evaluate_interview_answer, generate_interview_questions

router = APIRouter(prefix="/ai/interviews")


@router.post("/sessions", response_model=InterviewSessionOut, status_code=status.HTTP_201_CREATED)
def create_session(payload: InterviewSessionCreate, db: Session = Depends(get_db)):
    if not db.get(Member, payload.member_id):
        raise HTTPException(status_code=404, detail="Member not found")

    session = InterviewSession(
        member_id=payload.member_id,
        target_role=payload.target_role,
        num_questions=payload.num_questions,
        status="generating",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    generate_interview_questions.delay(session.id)
    # return with empty questions for now; client polls session detail
    return session


@router.get("/sessions", response_model=list[InterviewSessionOut])
def list_sessions(
    member_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(InterviewSession).options(selectinload(InterviewSession.questions))
    if member_id is not None:
        stmt = stmt.where(InterviewSession.member_id == member_id)
    sessions = (
        db.execute(stmt.order_by(InterviewSession.id.desc()).offset(offset).limit(limit))
        .scalars()
        .all()
    )
    return sessions


@router.get("/sessions/{session_id}", response_model=InterviewSessionOut)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = (
        db.execute(
            select(InterviewSession)
            .options(selectinload(InterviewSession.questions))
            .where(InterviewSession.id == session_id)
        )
        .scalars()
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.get("/sessions/{session_id}/questions", response_model=list[InterviewQuestionOut])
def list_questions(session_id: int, db: Session = Depends(get_db)):
    if not db.get(InterviewSession, session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    qs = (
        db.execute(
            select(InterviewQuestion)
            .where(InterviewQuestion.session_id == session_id)
            .order_by(InterviewQuestion.sort_order.asc())
        )
        .scalars()
        .all()
    )
    return qs


@router.post("/questions/{question_id}/answers", response_model=InterviewAnswerOut, status_code=status.HTTP_201_CREATED)
def submit_answer(question_id: int, payload: InterviewAnswerCreate, db: Session = Depends(get_db)):
    q = db.get(InterviewQuestion, question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")

    attempt = int(
        db.execute(
            select(func.count())
            .select_from(InterviewAnswer)
            .where(InterviewAnswer.question_id == question_id)
        ).scalar_one()
    ) + 1

    ans = InterviewAnswer(
        question_id=question_id,
        attempt=attempt,
        answer=payload.answer,
        status="pending",
    )
    db.add(ans)
    db.commit()
    db.refresh(ans)

    evaluate_interview_answer.delay(ans.id)
    return ans


@router.get("/questions/{question_id}/answers", response_model=list[InterviewAnswerOut])
def list_answers(question_id: int, db: Session = Depends(get_db)):
    if not db.get(InterviewQuestion, question_id):
        raise HTTPException(status_code=404, detail="Question not found")

    answers = (
        db.execute(
            select(InterviewAnswer)
            .where(InterviewAnswer.question_id == question_id)
            .order_by(InterviewAnswer.attempt.asc())
        )
        .scalars()
        .all()
    )
    return answers


@router.get("/answers/{answer_id}", response_model=InterviewAnswerOut)
def get_answer(answer_id: int, db: Session = Depends(get_db)):
    ans = db.get(InterviewAnswer, answer_id)
    if not ans:
        raise HTTPException(status_code=404, detail="Answer not found")
    return ans

