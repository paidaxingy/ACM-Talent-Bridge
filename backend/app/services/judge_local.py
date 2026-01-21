from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from app.models.problem import Testcase


@dataclass(frozen=True)
class JudgeResult:
    verdict: str  # AC/WA/CE/RE/TLE/SE
    time_ms: int | None = None
    memory_kb: int | None = None
    message: str | None = None


def _norm(s: str) -> str:
    # Normalize outputs similarly to many OJ: ignore trailing spaces and trailing newlines
    lines = [line.rstrip() for line in s.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def judge_python3(code: str, testcases: list[Testcase], *, time_limit_ms: int) -> JudgeResult:
    """
    MVP local judge for Python3.
    - Runs user code with stdin = testcase.input_data
    - Compares stdout with expected_output after normalization
    """

    if not testcases:
        return JudgeResult(verdict="SE", message="No testcases configured")

    timeout_s = max(0.1, time_limit_ms / 1000.0)

    with TemporaryDirectory(prefix="acm_judge_") as tmp:
        tmp_dir = Path(tmp)
        src = tmp_dir / "main.py"
        src.write_text(code, encoding="utf-8")

        max_time_ms: int = 0
        for idx, tc in enumerate(sorted(testcases, key=lambda t: t.sort_order), start=1):
            start = time.perf_counter()
            try:
                proc = subprocess.run(
                    ["python3", str(src)],
                    input=tc.input_data,
                    text=True,
                    capture_output=True,
                    timeout=timeout_s,
                )
            except subprocess.TimeoutExpired:
                return JudgeResult(verdict="TLE", time_ms=time_limit_ms, message=f"TLE on testcase #{idx}")

            elapsed_ms = int((time.perf_counter() - start) * 1000)
            max_time_ms = max(max_time_ms, elapsed_ms)

            if proc.returncode != 0:
                msg = (proc.stderr or "").strip()
                if msg:
                    msg = msg[:4000]
                return JudgeResult(verdict="RE", time_ms=max_time_ms, message=msg or f"RE on testcase #{idx}")

            out = _norm(proc.stdout or "")
            exp = _norm(tc.expected_output or "")
            if out != exp:
                return JudgeResult(verdict="WA", time_ms=max_time_ms, message=f"WA on testcase #{idx}")

        return JudgeResult(verdict="AC", time_ms=max_time_ms)

