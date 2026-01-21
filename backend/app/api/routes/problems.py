from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_admin
from app.models.lab import Lab
from app.models.problem import Problem, Testcase
from app.schemas.problem import (
    ProblemCreate,
    ProblemOut,
    ProblemUpdate,
    TestcaseCreate,
    TestcaseOut,
)

router = APIRouter(prefix="/problems")


@router.post("", response_model=ProblemOut, status_code=status.HTTP_201_CREATED)
def create_problem(payload: ProblemCreate, db: Session = Depends(get_db), _: object = Depends(require_admin)):
    lab_id = payload.lab_id
    if lab_id is None:
        # 产品层去掉 Lab：默认挂到第一个（启动时会自动确保存在）
        lab = db.execute(select(Lab).order_by(Lab.id.asc()).limit(1)).scalars().first()
        if not lab:
            raise HTTPException(status_code=500, detail="Default lab not initialized")
        lab_id = lab.id
    else:
        if not db.get(Lab, lab_id):
            raise HTTPException(status_code=404, detail="Lab not found")

    problem = Problem(
        lab_id=lab_id,
        title=payload.title,
        statement=payload.statement,
        input_desc=payload.input_desc,
        output_desc=payload.output_desc,
        time_limit_ms=payload.time_limit_ms,
        memory_limit_mb=payload.memory_limit_mb,
    )
    db.add(problem)
    db.commit()
    db.refresh(problem)
    return problem


@router.get("", response_model=list[ProblemOut])
def list_problems(
    lab_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Problem)
    if lab_id is not None:
        stmt = stmt.where(Problem.lab_id == lab_id)

    problems = (
        db.execute(stmt.order_by(Problem.id.desc()).offset(offset).limit(limit))
        .scalars()
        .all()
    )
    return problems


@router.get("/{problem_id}", response_model=ProblemOut)
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    problem = db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    return problem


@router.patch("/{problem_id}", response_model=ProblemOut)
def update_problem(
    problem_id: int,
    payload: ProblemUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    problem = db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    if payload.title is not None:
        problem.title = payload.title
    if payload.statement is not None:
        problem.statement = payload.statement
    if payload.input_desc is not None:
        problem.input_desc = payload.input_desc
    if payload.output_desc is not None:
        problem.output_desc = payload.output_desc
    if payload.time_limit_ms is not None:
        problem.time_limit_ms = payload.time_limit_ms
    if payload.memory_limit_mb is not None:
        problem.memory_limit_mb = payload.memory_limit_mb

    db.commit()
    db.refresh(problem)
    return problem


@router.delete("/{problem_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_problem(problem_id: int, db: Session = Depends(get_db), _: object = Depends(require_admin)):
    problem = db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    db.delete(problem)
    db.commit()
    return None


@router.post("/{problem_id}/testcases", response_model=TestcaseOut, status_code=status.HTTP_201_CREATED)
def add_testcase(
    problem_id: int,
    payload: TestcaseCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    if not db.get(Problem, problem_id):
        raise HTTPException(status_code=404, detail="Problem not found")

    tc = Testcase(
        problem_id=problem_id,
        input_data=payload.input_data,
        expected_output=payload.expected_output,
        is_sample=payload.is_sample,
        sort_order=payload.sort_order,
    )
    db.add(tc)
    try:
        db.commit()
    except IntegrityError:  # noqa: PERF203 (MVP)
        db.rollback()
        raise HTTPException(status_code=409, detail="sort_order already exists for this problem")

    db.refresh(tc)
    return tc


@router.get("/{problem_id}/testcases", response_model=list[TestcaseOut])
def list_testcases(problem_id: int, db: Session = Depends(get_db)):
    if not db.get(Problem, problem_id):
        raise HTTPException(status_code=404, detail="Problem not found")

    tcs = (
        db.execute(select(Testcase).where(Testcase.problem_id == problem_id).order_by(Testcase.sort_order.asc()))
        .scalars()
        .all()
    )
    return tcs


@router.delete("/{problem_id}/testcases/{testcase_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_testcase(
    problem_id: int,
    testcase_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    # Ensure problem exists (more user-friendly 404)
    if not db.get(Problem, problem_id):
        raise HTTPException(status_code=404, detail="Problem not found")

    tc = db.get(Testcase, testcase_id)
    if not tc or tc.problem_id != problem_id:
        raise HTTPException(status_code=404, detail="Testcase not found")

    db.delete(tc)
    db.commit()
    return None

