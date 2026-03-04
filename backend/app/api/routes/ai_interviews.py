from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.interview import InterviewAnswer, InterviewChatMessage, InterviewQuestion, InterviewSession
from app.models.member import Member
from app.models.user import User
from app.schemas.interview import (
    ChatMessageOut,
    ChatReplyIn,
    ChatReplyOut,
    ChatRoundSummaryOut,
    ChatSessionOut,
    ChatSessionStartIn,
    ChatSessionSummaryOut,
    InterviewAnswerCreate,
    InterviewAnswerOut,
    InterviewQuestionOut,
    InterviewQuestionSummaryOut,
    InterviewSessionCreate,
    InterviewSessionOut,
    InterviewSessionSummaryOut,
)
from app.services.ai_provider import get_ai_provider
from app.services.resume_parser import extract_resume_text
from app.tasks.ai_interview import evaluate_interview_answer, generate_interview_questions

router = APIRouter(prefix="/ai/interviews")
DEFAULT_CHAT_MAX_ROUNDS = 30


def _get_current_member(db: Session, user: User) -> Member:
    member = db.execute(select(Member).where(Member.handle == user.username)).scalars().first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found for current user")
    return member


def _require_pdf_resume(member: Member) -> None:
    if not member.resume_url:
        raise HTTPException(status_code=400, detail="请先上传 PDF 简历后再开始面试")
    if not member.resume_url.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 简历，请先上传 PDF 格式简历")


def _ensure_session_access(db: Session, user: User, session_id: int) -> InterviewSession:
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

    if user.role != "admin":
        member = _get_current_member(db, user)
        if session.member_id != member.id:
            raise HTTPException(status_code=403, detail="No permission to access this session")
    return session


def _chat_session_out(session: InterviewSession) -> ChatSessionOut:
    return ChatSessionOut(
        id=session.id,
        member_id=session.member_id,
        status=session.status,
        target_role=session.target_role,
        num_rounds=session.num_questions,
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


def _is_repetitive_followup(current_question: str, next_question: str | None) -> bool:
    if not next_question:
        return False
    c = current_question.strip()
    n = next_question.strip()
    if not n:
        return False
    if n == c:
        return True
    if n in {"请继续说明你在该项目中的关键技术权衡。", "请继续说明你在该项目中的关键技术权衡"}:
        return True
    return False


def _build_non_repetitive_followup(candidate_answer: str) -> str:
    if len((candidate_answer or "").strip()) < 80:
        return "请用一个具体实例展开说明：你如何构造输入、如何验证输出、如何定位偏差，以及最终结果是什么？"
    return "你提到了测试与比对，请进一步说明你在精度、性能和可维护性之间做过哪些权衡，并给出一次真实决策过程。"


@router.post("/sessions", response_model=InterviewSessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    payload: InterviewSessionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        get_ai_provider()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    member = _get_current_member(db, user)
    _require_pdf_resume(member)

    session = InterviewSession(
        member_id=member.id,
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


@router.post("/chat/sessions/start", response_model=ChatSessionOut, status_code=status.HTTP_201_CREATED)
def start_chat_session(
    payload: ChatSessionStartIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    provider = get_ai_provider()
    member = _get_current_member(db, user)
    _require_pdf_resume(member)
    resume_text = extract_resume_text(member)
    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="未读取到有效简历文本（可能是扫描件或图片版 PDF），请上传可复制文字的 PDF 简历",
        )

    from app.services.member_profile import build_member_profile_summary

    profile = build_member_profile_summary(db, member.id).to_dict()
    try:
        first_q = provider.start_chat_interview(
            profile,
            target_role=payload.target_role,
            resume_text=resume_text,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    if not first_q.question:
        raise HTTPException(status_code=500, detail="AI 未返回有效首轮问题")

    session = InterviewSession(
        member_id=member.id,
        target_role=payload.target_role,
        num_questions=DEFAULT_CHAT_MAX_ROUNDS,
        status="in_progress",
    )
    db.add(session)
    db.flush()
    db.add(
        InterviewChatMessage(
            session_id=session.id,
            round_no=1,
            role="interviewer",
            content=first_q.question,
            difficulty=first_q.difficulty or "medium",
        )
    )
    db.commit()
    db.refresh(session)
    return _chat_session_out(session)


@router.get("/chat/sessions", response_model=list[ChatSessionOut])
def list_chat_sessions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(InterviewSession).order_by(InterviewSession.id.desc()).offset(offset).limit(limit)
    if user.role != "admin":
        member = _get_current_member(db, user)
        stmt = stmt.where(InterviewSession.member_id == member.id)
    sessions = db.execute(stmt).scalars().all()
    return [_chat_session_out(s) for s in sessions]


@router.get("/chat/sessions/{session_id}/messages", response_model=list[ChatMessageOut])
def list_chat_messages(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ensure_session_access(db, user, session_id)
    msgs = (
        db.execute(
            select(InterviewChatMessage)
            .where(InterviewChatMessage.session_id == session_id)
            .order_by(InterviewChatMessage.round_no.asc(), InterviewChatMessage.id.asc())
        )
        .scalars()
        .all()
    )
    return msgs


@router.post("/chat/sessions/{session_id}/reply", response_model=ChatReplyOut)
def chat_reply(
    session_id: int,
    payload: ChatReplyIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    provider = get_ai_provider()
    session = _ensure_session_access(db, user, session_id)
    if session.status == "completed":
        raise HTTPException(status_code=400, detail="面试已结束，请重新创建会话")

    member = db.get(Member, session.member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    _require_pdf_resume(member)
    resume_text = extract_resume_text(member)
    if not resume_text:
        raise HTTPException(
            status_code=400,
            detail="未读取到有效简历文本（可能是扫描件或图片版 PDF），请上传可复制文字的 PDF 简历",
        )

    from app.services.member_profile import build_member_profile_summary

    profile = build_member_profile_summary(db, member.id).to_dict()

    msgs = (
        db.execute(
            select(InterviewChatMessage)
            .where(InterviewChatMessage.session_id == session_id)
            .order_by(InterviewChatMessage.round_no.asc(), InterviewChatMessage.id.asc())
        )
        .scalars()
        .all()
    )
    current_question = next((m for m in reversed(msgs) if m.role == "interviewer"), None)
    if not current_question:
        raise HTTPException(status_code=400, detail="当前会话没有可回答的问题")

    round_no = current_question.round_no
    if round_no > session.num_questions:
        session.status = "completed"
        db.commit()
        raise HTTPException(status_code=400, detail="面试轮次已达到上限，请结束会话")

    history = [{"role": m.role, "content": m.content} for m in msgs]
    is_last_round = round_no >= session.num_questions
    try:
        eva = provider.evaluate_and_followup(
            profile,
            target_role=session.target_role,
            resume_text=resume_text,
            history=history,
            current_question=current_question.content,
            candidate_answer=payload.answer,
            is_last_round=is_last_round,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))

    candidate_msg = InterviewChatMessage(
        session_id=session.id,
        round_no=round_no,
        role="candidate",
        content=payload.answer.strip(),
        score=max(0, min(100, int(eva.score))),
        standard_answer=eva.standard_answer,
        strengths=eva.strengths,
        weaknesses=eva.weaknesses,
        suggestions=eva.suggestions,
    )
    db.add(candidate_msg)

    next_question_msg = None
    if not is_last_round and eva.next_question:
        next_q = eva.next_question.strip()
        if _is_repetitive_followup(current_question.content, next_q):
            next_q = _build_non_repetitive_followup(payload.answer)
        next_question_msg = InterviewChatMessage(
            session_id=session.id,
            round_no=round_no + 1,
            role="interviewer",
            content=next_q,
            difficulty=(eva.next_difficulty or "medium"),
        )
        db.add(next_question_msg)
        session.status = "in_progress"
    else:
        session.status = "completed"

    db.commit()
    db.refresh(session)
    db.refresh(candidate_msg)
    if next_question_msg is not None:
        db.refresh(next_question_msg)

    return ChatReplyOut(
        session=_chat_session_out(session),
        candidate_message=ChatMessageOut.model_validate(candidate_msg),
        next_question=(ChatMessageOut.model_validate(next_question_msg) if next_question_msg else None),
    )


@router.post("/chat/sessions/{session_id}/finish", response_model=ChatSessionSummaryOut)
def finish_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = _ensure_session_access(db, user, session_id)
    session.status = "completed"
    db.commit()
    return get_chat_summary(session_id, db, user)


@router.get("/chat/sessions/{session_id}/summary", response_model=ChatSessionSummaryOut)
def get_chat_summary(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = _ensure_session_access(db, user, session_id)
    msgs = (
        db.execute(
            select(InterviewChatMessage)
            .where(InterviewChatMessage.session_id == session_id)
            .order_by(InterviewChatMessage.round_no.asc(), InterviewChatMessage.id.asc())
        )
        .scalars()
        .all()
    )

    interviewer_map: dict[int, InterviewChatMessage] = {}
    candidate_map: dict[int, InterviewChatMessage] = {}
    for m in msgs:
        if m.role == "interviewer":
            interviewer_map[m.round_no] = m
        elif m.role == "candidate":
            candidate_map[m.round_no] = m

    rounds: list[ChatRoundSummaryOut] = []
    weight_map = {"easy": 1.0, "medium": 1.5, "hard": 2.0}
    weighted_sum = 0.0
    weight_total = 0.0
    answered_rounds = 0

    for round_no in sorted(interviewer_map.keys()):
        q = interviewer_map[round_no]
        a = candidate_map.get(round_no)
        diff = (q.difficulty or "medium").lower()
        w = weight_map.get(diff, 1.0)
        weight_total += w
        if a and a.score is not None:
            answered_rounds += 1
            weighted_sum += a.score * w

        rounds.append(
            ChatRoundSummaryOut(
                round_no=round_no,
                question=q.content,
                difficulty=q.difficulty,
                answer=a.content if a else None,
                score=a.score if a else None,
                standard_answer=a.standard_answer if a else None,
                strengths=a.strengths if a else None,
                weaknesses=a.weaknesses if a else None,
                suggestions=a.suggestions if a else None,
            )
        )

    total_score = round(weighted_sum / weight_total, 2) if weight_total > 0 else 0.0
    return ChatSessionSummaryOut(
        session_id=session.id,
        status=session.status,
        total_rounds=session.num_questions,
        answered_rounds=answered_rounds,
        total_score=total_score,
        rounds=rounds,
    )


@router.get("/sessions", response_model=list[InterviewSessionOut])
def list_sessions(
    member_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(InterviewSession).options(selectinload(InterviewSession.questions))
    if user.role == "admin" and member_id is not None:
        stmt = stmt.where(InterviewSession.member_id == member_id)
    elif user.role != "admin":
        member = _get_current_member(db, user)
        stmt = stmt.where(InterviewSession.member_id == member.id)
    sessions = (
        db.execute(stmt.order_by(InterviewSession.id.desc()).offset(offset).limit(limit))
        .scalars()
        .all()
    )
    return sessions


@router.get("/sessions/{session_id}", response_model=InterviewSessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return _ensure_session_access(db, user, session_id)


@router.get("/sessions/{session_id}/questions", response_model=list[InterviewQuestionOut])
def list_questions(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _ensure_session_access(db, user, session_id)

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
def submit_answer(
    question_id: int,
    payload: InterviewAnswerCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.get(InterviewQuestion, question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    _ensure_session_access(db, user, q.session_id)

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
def list_answers(
    question_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.get(InterviewQuestion, question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    _ensure_session_access(db, user, q.session_id)

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
def get_answer(
    answer_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ans = db.get(InterviewAnswer, answer_id)
    if not ans:
        raise HTTPException(status_code=404, detail="Answer not found")
    q = db.get(InterviewQuestion, ans.question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    _ensure_session_access(db, user, q.session_id)
    return ans


@router.get("/sessions/{session_id}/summary", response_model=InterviewSessionSummaryOut)
def get_session_summary(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = _ensure_session_access(db, user, session_id)
    questions = (
        db.execute(
            select(InterviewQuestion)
            .options(selectinload(InterviewQuestion.answers))
            .where(InterviewQuestion.session_id == session.id)
            .order_by(InterviewQuestion.sort_order.asc())
        )
        .scalars()
        .all()
    )

    weight_map = {"easy": 1.0, "medium": 1.5, "hard": 2.0}
    total_weight = 0.0
    weighted_score = 0.0
    answered_questions = 0
    summary_questions: list[InterviewQuestionSummaryOut] = []

    for q in questions:
        latest = max(q.answers, key=lambda x: x.attempt) if q.answers else None
        weight = weight_map.get((q.difficulty or "").lower(), 1.0)
        total_weight += weight

        latest_score = latest.score if latest and latest.score is not None else None
        if latest_score is not None:
            answered_questions += 1
            weighted_score += latest_score * weight

        summary_questions.append(
            InterviewQuestionSummaryOut(
                question_id=q.id,
                sort_order=q.sort_order,
                topic=q.topic,
                difficulty=q.difficulty,
                question=q.question,
                standard_answer=q.standard_answer,
                latest_attempt=latest.attempt if latest else None,
                latest_score=latest_score,
                strengths=latest.strengths if latest else None,
                weaknesses=latest.weaknesses if latest else None,
                suggestions=latest.suggestions if latest else None,
            )
        )

    # 未回答题目按 0 分计入总分，确保总分反映完整面试表现
    final_score = 0.0
    if total_weight > 0:
        final_score = round(weighted_score / total_weight, 2)

    return InterviewSessionSummaryOut(
        session_id=session.id,
        total_questions=len(questions),
        answered_questions=answered_questions,
        total_score=final_score,
        questions=summary_questions,
    )

