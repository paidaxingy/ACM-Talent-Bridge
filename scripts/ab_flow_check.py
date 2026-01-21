#!/usr/bin/env python3
from __future__ import annotations

"""
End-to-end check for BE-P0-B04：A+B 测试赛闭环验证（后端自测用）。

流程：
1. 注册并登录两个学生用户，获得 token
2. 创建队伍、邀请队友加入
3. 找到名为 "A+B 测试赛" 的竞赛，并获取其中的 A 题（A + B Problem）
4. 以该队伍报名参赛
5. 提交一份正确的 A+B 解答，轮询直到评测完成
6. 拉取 /submissions 与 /contests/{id}/scoreboard，检查：
   - 至少有一条 AC 提交
   - 榜单上该队 solved>=1

运行方式（后端已在 http://localhost:8000 运行时）：

    cd /home/yzt/workspace/ACM-Talent-Bridge
    python3 scripts/ab_flow_check.py
"""

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib import error, request


BASE = os.environ.get("ACM_BRIDGE_API", "http://localhost:8000/api/v1").rstrip("/")


@dataclass
class Resp:
    status: int
    data: Any
    raw: str


def _req(
    method: str,
    path: str,
    payload: dict | None = None,
    token: str | None = None,
) -> Resp:
    url = f"{BASE}{path}"
    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, data=data, method=method, headers=headers)

    try:
        with request.urlopen(req, timeout=20) as r:  # noqa: S310
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


def must_ok(r: Resp, expect: int | tuple[int, ...]) -> Resp:
    exp = (expect,) if isinstance(expect, int) else expect
    if r.status not in exp:
        raise RuntimeError(f"HTTP {r.status}: {r.raw}")
    return r


def wait_submission_done(sub_id: int, token: str, timeout_s: int = 20) -> dict:
    deadline = time.time() + timeout_s
    last: dict | None = None
    while time.time() < deadline:
        r = must_ok(get(f"/submissions/{sub_id}", token=token), 200)
        last = r.data
        if isinstance(last, dict) and last.get("status") == "done":
            return last
        time.sleep(0.5)
    raise TimeoutError(f"Submission {sub_id} not done, last={last}")


def main() -> None:
    print(f"[ab-flow] base={BASE}")

    # 1. 准备两个学生账号
    suffix = str(int(time.time()))
    alice_u = f"ab_fe_alice_{suffix}"
    bob_u = f"ab_fe_bob_{suffix}"
    pwd = "password123"

    for uname in (alice_u, bob_u):
        r_reg = post("/auth/register", {"username": uname, "password": pwd})
        if r_reg.status not in (201, 409):
            raise RuntimeError(f"register {uname} failed: {r_reg.raw}")

    alice_token = must_ok(
        post("/auth/login", {"username": alice_u, "password": pwd}),
        200,
    ).data["access_token"]
    bob_token = must_ok(
        post("/auth/login", {"username": bob_u, "password": pwd}),
        200,
    ).data["access_token"]
    print(f"[ab-flow] users ready: {alice_u}, {bob_u}")

    # 2. Alice 创建队伍，Bob 加入
    team = must_ok(
        post("/teams", {"team_name": f"ab-team-{suffix}"}, token=alice_token),
        201,
    ).data
    team_id = int(team["team_id"])
    print(f"[ab-flow] team_id={team_id}")

    must_ok(post(f"/teams/{team_id}/join", token=bob_token), 200)
    print("[ab-flow] bob joined team")

    # 3. 找到 “A+B 测试赛” + A 题
    contests = must_ok(get("/contests?limit=200", token=alice_token), 200).data or []
    ab_contest = next(
        (c for c in contests if isinstance(c, dict) and c.get("name") == "A+B 测试赛"),
        None,
    )
    if not ab_contest:
        raise RuntimeError("Cannot find contest named 'A+B 测试赛'. 请先运行 scripts/setup_ab_contest.py")

    contest_id = int(ab_contest["id"])
    print(f"[ab-flow] contest_id={contest_id}")

    problems = must_ok(
        get(f"/contests/{contest_id}/problems/detail", token=alice_token),
        200,
    ).data or []
    if not problems:
        raise RuntimeError("Contest has no problems. 请检查 A+B 题是否已加入竞赛。")

    # 取第一题作为 A
    p0 = problems[0]
    problem_id = int(p0["problem_id"])
    print(f"[ab-flow] problem_id={problem_id}, letter={p0.get('problem_letter')}, title={p0.get('problem_title')}")

    # 4. 队伍报名
    must_ok(
        post(
            f"/contests/{contest_id}/register",
            {"team_id": team_id},
            token=alice_token,
        ),
        (201, 409),  # 409 表示已报名过，也算通过
    )
    print("[ab-flow] team registered contest")

    # 5. 提交一份正确解答
    code = "a,b=map(int,input().split());print(a+b)\n"
    sub = must_ok(
        post(
            "/submissions",
            {
                "problem_id": problem_id,
                "contest_id": contest_id,
                "team_id": team_id,
                "language": "python3",
                "code": code,
            },
            token=alice_token,
        ),
        201,
    ).data
    sub_id = int(sub["id"])
    print(f"[ab-flow] submission_id={sub_id}")

    res = wait_submission_done(sub_id, token=alice_token, timeout_s=40)
    print(f"[ab-flow] submission verdict={res.get('verdict')}, time_ms={res.get('time_ms')}")
    if res.get("message"):
        print(f"[ab-flow] submission message={res.get('message')}")
    if res.get("verdict") != "AC":
        raise RuntimeError("Submission verdict is not AC，详见上方 message 日志，请检查判题配置或用户代码。")

    # 6. 检查榜单
    board = must_ok(
        get(f"/contests/{contest_id}/scoreboard", token=alice_token),
        200,
    ).data
    rows = board.get("rows") or []
    target = next((r for r in rows if r.get("team_id") == team_id), None)
    if not target:
        raise RuntimeError("Scoreboard has no row for this team, 请检查报名与提交逻辑。")
    print(f"[ab-flow] team row: solved={target.get('solved')}, penalty={target.get('penalty_minutes')}")
    if int(target.get("solved") or 0) < 1:
        raise RuntimeError("Scoreboard shows solved<1 for this team, 与预期不符。")

    print("[ab-flow] OK: A+B 测试赛闭环验证通过。")


if __name__ == "__main__":
    main()

