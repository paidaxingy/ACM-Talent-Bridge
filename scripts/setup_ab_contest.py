#!/usr/bin/env python3
from __future__ import annotations

"""
Setup script for section 11: A+B 示例题目与测试赛.

- 创建（或复用）一个 Lab
- 创建（或复用）题目 "A + B Problem" 以及样例测试点
- 创建（或复用）竞赛 "A+B 测试赛"，并将题目作为 A 题加入，状态置为 running

运行方式（默认后端地址 http://localhost:8000/api/v1）：

    cd /home/yzt/workspace/ACM-Talent-Bridge
    python3 scripts/setup_ab_contest.py
"""

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib import error, request


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
    req = request.Request(url=url, data=data, method=method, headers=headers)

    try:
        with request.urlopen(req, timeout=20) as r:  # noqa: S310 (trusted local API)
            raw = r.read().decode("utf-8")
            try:
                parsed = json.loads(raw) if raw else None
            except Exception:
                parsed = raw
            return Resp(status=r.status, data=parsed, raw=raw)
    except error.HTTPError as e:
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


def patch(path: str, payload: dict | None = None, token: str | None = None) -> Resp:
    return _req("PATCH", path, payload=payload, token=token)


def must_ok(r: Resp, expect: int | tuple[int, ...]) -> Resp:
    exp = (expect,) if isinstance(expect, int) else expect
    if r.status not in exp:
        raise RuntimeError(f"HTTP {r.status}: {r.raw}")
    return r


def ensure_lab() -> int:
    """Find or create a lab for A+B tests."""
    r = must_ok(get("/labs?limit=200"), 200)
    labs = r.data or []
    for lab in labs:
        if isinstance(lab, dict) and lab.get("name") == "ab-test-lab":
            return int(lab["id"])

    lab = must_ok(
        post(
            "/labs",
            {"name": "ab-test-lab", "description": "Lab for A+B sample contest"},
        ),
        201,
    ).data
    return int(lab["id"])


def ensure_problem(lab_id: int) -> int:
    """Find or create 'A + B Problem' under given lab."""
    r = must_ok(get(f"/problems?lab_id={lab_id}&limit=200"), 200)
    probs = r.data or []
    for p in probs:
        if isinstance(p, dict) and p.get("title") == "A + B Problem":
            return int(p["id"])

    statement = (
        "给定两个整数 a, b，输出它们的和 a + b。\n\n"
        "输入包含一行，包含两个整数 a, b（以空格分隔）。\n"
        "-10^9 ≤ a, b ≤ 10^9。"
    )
    prob = must_ok(
        post(
            "/problems",
            {
                "lab_id": lab_id,
                "title": "A + B Problem",
                "statement": statement,
                "input_desc": "一行，两个整数 a, b，以空格分隔。",
                "output_desc": "输出一个整数，即 a + b。",
                "time_limit_ms": 2000,
                "memory_limit_mb": 256,
            },
        ),
        201,
    ).data
    return int(prob["id"])


def ensure_sample_testcase(problem_id: int) -> None:
    """Ensure there is at least one sample testcase 1 2 -> 3."""
    r = must_ok(get(f"/problems/{problem_id}/testcases"), 200)
    tcs = r.data or []
    for tc in tcs:
        if (
            isinstance(tc, dict)
            and tc.get("is_sample")
            and tc.get("input_data") == "1 2\n"
        ):
            return

    must_ok(
        post(
            f"/problems/{problem_id}/testcases",
            {
                "input_data": "1 2\n",
                "expected_output": "3\n",
                "is_sample": True,
                "sort_order": 1,
            },
        ),
        201,
    )


def ensure_contest(lab_id: int, token: str) -> int:
    """Find or create 'A+B 测试赛' contest for the given lab."""
    r = must_ok(get("/contests?limit=200", token=token), 200)
    contests = r.data or []
    for c in contests:
        if (
            isinstance(c, dict)
            and c.get("lab_id") == lab_id
            and c.get("name") == "A+B 测试赛"
        ):
            return int(c["id"])

    contest = must_ok(
        post(
            "/contests",
            {
                "lab_id": lab_id,
                "name": "A+B 测试赛",
                "contest_type": "training",
                "description": "用于验证整条链路的最小测试赛（A + B Problem）",
                "status": "draft",
                "start_at": None,
                "end_at": None,
            },
            token=token,
        ),
        201,
    ).data
    return int(contest["id"])


def ensure_contest_problem(contest_id: int, problem_id: int, token: str) -> None:
    """Ensure the contest has the given problem as A (sort_order=1).

    直接尝试插入 (contest_id, problem_id)；若已存在（409）则视为成功，便于脚本幂等。
    """
    r = post(
        f"/contests/{contest_id}/problems",
        {"problem_id": problem_id, "sort_order": 1, "score": 100},
        token=token,
    )
    if r.status not in (201, 409):
        raise RuntimeError(f"Failed to ensure contest problem: HTTP {r.status}: {r.raw}")


def ensure_contest_running(contest_id: int) -> None:
    """Set contest status to running（幂等），不再先 GET，避免 draft 对 student 404 的问题。"""
    r = patch(
        f"/contests/{contest_id}",
        {"status": "running"},
        token=TOKEN_AB_SETUP,
    )
    if r.status not in (200,):
        raise RuntimeError(f"Failed to set contest running: HTTP {r.status}: {r.raw}")


def main() -> None:
    print(f"[setup-ab] base={BASE}")

    # contests 路由已经要求鉴权，这里快速创建一个专用用户拿 token
    global TOKEN_AB_SETUP  # noqa: PLW0603
    username = "ab_setup_user"
    password = "password123"
    # 注册可能 201 或 409（已存在）都算成功
    r_reg = post(
        "/auth/register",
        {"username": username, "password": password},
    )
    if r_reg.status not in (201, 409):
        raise RuntimeError(f"Failed to ensure setup user: {r_reg.raw}")
    r_login = must_ok(
        post("/auth/login", {"username": username, "password": password}),
        200,
    )
    TOKEN_AB_SETUP = r_login.data["access_token"]
    print("[setup-ab] auth user ready for contests API")

    lab_id = ensure_lab()
    print(f"[setup-ab] lab_id={lab_id}")

    problem_id = ensure_problem(lab_id)
    print(f"[setup-ab] problem_id={problem_id} title='A + B Problem'")

    ensure_sample_testcase(problem_id)
    print("[setup-ab] sample testcase ensured (1 2 -> 3)")

    contest_id = ensure_contest(lab_id, token=TOKEN_AB_SETUP)
    print(f"[setup-ab] contest_id={contest_id} name='A+B 测试赛'")

    ensure_contest_problem(contest_id, problem_id, token=TOKEN_AB_SETUP)
    print("[setup-ab] contest_problems ensured (A = A + B Problem)")

    ensure_contest_running(contest_id)
    print("[setup-ab] contest status set to 'running'")

    print(
        "[setup-ab] DONE. You can use this for FE/BE E2E flow:\n"
        f"  - lab_id={lab_id}\n"
        f"  - problem_id={problem_id}\n"
        f"  - contest_id={contest_id}\n"
    )


if __name__ == "__main__":
    main()

