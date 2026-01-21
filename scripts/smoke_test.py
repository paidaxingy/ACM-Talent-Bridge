#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import uuid4


BASE = os.environ.get("ACM_BRIDGE_API", "http://localhost:8000/api/v1").rstrip("/")


@dataclass
class Resp:
    status: int
    data: Any
    raw: str


def _req(method: str, path: str, payload: dict | None = None, token: str | None = None) -> Resp:
    url = f"{BASE}{path}"
    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url=url, data=data, method=method, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode("utf-8")
            try:
                parsed = json.loads(raw) if raw else None
            except Exception:
                parsed = raw
            return Resp(status=r.status, data=parsed, raw=raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            parsed = json.loads(raw) if raw else None
        except Exception:
            parsed = raw
        return Resp(status=e.code, data=parsed, raw=raw)


def get(path: str, token: str | None = None) -> Resp:
    return _req("GET", path, token=token)


def post(path: str, payload: dict | None = None, token: str | None = None) -> Resp:
    return _req("POST", path, payload=payload, token=token)


def _must_ok(r: Resp, expect: int | tuple[int, ...] = (200, 201, 202)) -> Resp:
    exp = (expect,) if isinstance(expect, int) else expect
    if r.status not in exp:
        raise RuntimeError(f"HTTP {r.status}: {r.raw}")
    return r


def wait_submission_done(sub_id: int, timeout_s: int = 20) -> dict:
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        r = _must_ok(get(f"/submissions/{sub_id}", token=TOKEN_ALICE), 200)
        last = r.data
        if isinstance(last, dict) and last.get("status") == "done":
            return last
        time.sleep(0.5)
    raise TimeoutError(f"Submission {sub_id} not done, last={last}")


def wait_interview_ready(session_id: int, timeout_s: int = 20) -> dict:
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        r = _must_ok(get(f"/ai/interviews/sessions/{session_id}"), 200)
        last = r.data
        status = last.get("status") if isinstance(last, dict) else None
        if status in {"ready", "failed"}:
            return last
        time.sleep(0.5)
    raise TimeoutError(f"Interview session {session_id} not ready, last={last}")


def wait_answer_done(answer_id: int, timeout_s: int = 20) -> dict:
    deadline = time.time() + timeout_s
    last = None
    while time.time() < deadline:
        r = _must_ok(get(f"/ai/interviews/answers/{answer_id}"), 200)
        last = r.data
        status = last.get("status") if isinstance(last, dict) else None
        if status in {"done", "failed"}:
            return last
        time.sleep(0.5)
    raise TimeoutError(f"Answer {answer_id} not done, last={last}")


def main() -> None:
    print(f"[smoke] base={BASE}")

    # health
    _must_ok(get("/health"), 200)

    suffix = uuid4().hex[:8]

    # auth users (team-based contest flow needs Bearer token)
    global TOKEN_ALICE, TOKEN_BOB  # noqa: PLW0603
    alice_u = f"alice_{suffix}"
    bob_u = f"bob_{suffix}"
    pwd = "password123"
    _must_ok(post("/auth/register", {"username": alice_u, "password": pwd}), 201)
    _must_ok(post("/auth/register", {"username": bob_u, "password": pwd}), 201)
    TOKEN_ALICE = _must_ok(post("/auth/login", {"username": alice_u, "password": pwd}), 200).data["access_token"]
    TOKEN_BOB = _must_ok(post("/auth/login", {"username": bob_u, "password": pwd}), 200).data["access_token"]
    print("[auth] alice/bob tokens ready")

    # lab
    lab = _must_ok(
        post(
            "/labs",
            {"name": f"acm-lab-{suffix}", "description": "smoke test"},
        ),
        201,
    ).data
    lab_id = int(lab["id"])
    print(f"[lab] id={lab_id}")

    # members
    alice = _must_ok(
        post(
            "/members",
            {
                "lab_id": lab_id,
                "handle": f"alice_{suffix}",
                "group_name": "A",
                "tier": 1,
                "rating": 1500,
                "is_active": True,
            },
        ),
        201,
    ).data
    bob = _must_ok(
        post(
            "/members",
            {
                "lab_id": lab_id,
                "handle": f"bob_{suffix}",
                "group_name": "B",
                "tier": 1,
                "rating": 1500,
                "is_active": True,
            },
        ),
        201,
    ).data
    alice_id = int(alice["id"])
    bob_id = int(bob["id"])
    print(f"[members] alice={alice_id}, bob={bob_id}")

    # problem + testcase
    prob = _must_ok(
        post(
            "/problems",
            {
                "lab_id": lab_id,
                "title": f"Echo-{suffix}",
                "statement": "Read a line and output it.",
                "input_desc": "One line.",
                "output_desc": "The same line.",
                "time_limit_ms": 2000,
                "memory_limit_mb": 256,
            },
        ),
        201,
    ).data
    prob_id = int(prob["id"])
    _must_ok(
        post(
            f"/problems/{prob_id}/testcases",
            {"input_data": "hello\n", "expected_output": "hello\n", "is_sample": True, "sort_order": 1},
        ),
        201,
    )
    print(f"[problem] id={prob_id} testcase=1")

    # contest
    contest = _must_ok(
        post(
            "/contests",
            {
                "lab_id": lab_id,
                "name": f"Smoke Contest {suffix}",
                "contest_type": "training",
                "description": "smoke",
                "status": "running",
                "start_at": None,
                "end_at": None,
            },
        ),
        201,
    ).data
    contest_id = int(contest["id"])
    _must_ok(post(f"/contests/{contest_id}/problems", {"problem_id": prob_id, "sort_order": 1, "score": 100}), 201)

    # teams (user-side)
    team = _must_ok(post("/teams", {"team_name": f"team_{suffix}"}, token=TOKEN_ALICE), 201).data
    team_id = int(team["team_id"])
    _must_ok(post(f"/teams/{team_id}/join", token=TOKEN_BOB), 200)
    _must_ok(post(f"/contests/{contest_id}/register", {"team_id": team_id}, token=TOKEN_ALICE), 201)
    print(f"[contest] id={contest_id} + problem + team_registration team_id={team_id}")

    # submissions
    good_code = "print(input())\n"
    bad_code = "print('x')\n"

    s1 = _must_ok(
        post(
            "/submissions",
            {"team_id": team_id, "problem_id": prob_id, "contest_id": contest_id, "language": "python3", "code": good_code},
            token=TOKEN_ALICE,
        ),
        201,
    ).data
    s2 = _must_ok(
        post(
            "/submissions",
            {"team_id": team_id, "problem_id": prob_id, "contest_id": contest_id, "language": "python3", "code": bad_code},
            token=TOKEN_BOB,
        ),
        201,
    ).data
    s1_id = int(s1["id"])
    s2_id = int(s2["id"])
    print(f"[submit] alice_submission={s1_id}, bob_submission={s2_id}")

    r1 = wait_submission_done(s1_id)
    r2 = wait_submission_done(s2_id)
    print(f"[judge] alice verdict={r1.get('verdict')} time_ms={r1.get('time_ms')}")
    print(f"[judge] bob   verdict={r2.get('verdict')} time_ms={r2.get('time_ms')}")

    # scoreboard
    board = _must_ok(get(f"/contests/{contest_id}/scoreboard", token=TOKEN_ALICE), 200).data
    print(f"[scoreboard] rows={len(board.get('rows', []))}")

    # PK
    match = _must_ok(
        post(
            "/pk/matches",
            {"lab_id": lab_id, "title": "smoke pk", "teams": [[alice_id], [bob_id]]},
        ),
        201,
    ).data
    match_id = int(match["id"])
    _must_ok(post(f"/pk/matches/{match_id}/finish", {"winner_team_no": 1, "is_draw": False}), 200)
    members = _must_ok(get(f"/members?lab_id={lab_id}"), 200).data
    # find ratings
    rating_map = {m["id"]: m["rating"] for m in members}
    print(f"[pk] match={match_id} alice_rating={rating_map.get(alice_id)} bob_rating={rating_map.get(bob_id)}")

    # external contests refresh (best-effort)
    ref = post("/external/contests/refresh")
    if ref.status in (200, 202):
        task_id = ref.data.get("task_id") if isinstance(ref.data, dict) else None
        print(f"[external] refresh task_id={task_id}")
        time.sleep(2)
        ext = get("/external/contests")
        if ext.status == 200:
            print(f"[external] upcoming={len(ext.data)}")
        else:
            print(f"[external] list failed: HTTP {ext.status}")
    else:
        print(f"[external] refresh failed: HTTP {ref.status}")

    # AI interview (mock by default)
    sess = _must_ok(post("/ai/interviews/sessions", {"member_id": alice_id, "target_role": "backend", "num_questions": 3}), 201).data
    session_id = int(sess["id"])
    session = wait_interview_ready(session_id)
    print(f"[ai] session={session_id} status={session.get('status')}")
    if session.get("status") == "ready":
        qs = _must_ok(get(f"/ai/interviews/sessions/{session_id}/questions"), 200).data
        q1 = qs[0]
        qid = int(q1["id"])
        ans = _must_ok(post(f"/ai/interviews/questions/{qid}/answers", {"answer": "我会先说思路，再分析复杂度，最后处理边界情况并举例。"}), 201).data
        aid = int(ans["id"])
        eva = wait_answer_done(aid)
        print(f"[ai] answer={aid} status={eva.get('status')} score={eva.get('score')}")

    # profile
    prof = _must_ok(get(f"/members/{alice_id}/profile"), 200).data
    print(f"[profile] interview_avg_score={prof.get('interview_avg_score')} directions={len(prof.get('recommended_directions', []))}")

    print("[smoke] OK")


if __name__ == "__main__":
    main()
