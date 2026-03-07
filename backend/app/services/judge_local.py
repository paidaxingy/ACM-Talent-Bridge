from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from app.models.problem import Testcase

STDIO_MAX_LEN = 20_000
MESSAGE_MAX_LEN = 4_000


@dataclass(frozen=True)
class JudgeResult:
    verdict: str  # AC/WA/CE/RE/TLE/SE
    time_ms: int | None = None
    memory_kb: int | None = None
    message: str | None = None


@dataclass(frozen=True)
class RunResult:
    verdict: str  # OK/CE/RE/TLE/SE
    stdout: str = ""
    stderr: str = ""
    time_ms: int | None = None
    memory_kb: int | None = None
    message: str | None = None


@dataclass(frozen=True)
class _RawRunResult:
    verdict: str
    stdout: str = ""
    stderr: str = ""
    time_ms: int | None = None
    memory_kb: int | None = None
    message: str | None = None


def _truncate(text: str | None, limit: int) -> str:
    return (text or "")[:limit]


def _norm(s: str) -> str:
    lines = [line.rstrip() for line in s.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _run_python3_once_raw(code: str, stdin_text: str, *, time_limit_ms: int) -> _RawRunResult:
    timeout_s = max(0.1, time_limit_ms / 1000.0)

    with TemporaryDirectory(prefix="acm_run_") as tmp:
        tmp_dir = Path(tmp)
        src = tmp_dir / "main.py"
        src.write_text(code, encoding="utf-8")

        start = time.perf_counter()
        try:
            proc = subprocess.run(
                ["python3", str(src)],
                input=stdin_text,
                text=True,
                capture_output=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired as exc:
            return _RawRunResult(
                verdict="TLE",
                stdout=getattr(exc, "stdout", None) or "",
                stderr=getattr(exc, "stderr", None) or "",
                time_ms=time_limit_ms,
                message="Execution timed out",
            )

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        if proc.returncode != 0:
            message = _truncate((stderr or "").strip(), MESSAGE_MAX_LEN) or "Runtime Error"
            return _RawRunResult(
                verdict="RE",
                stdout=stdout,
                stderr=stderr,
                time_ms=elapsed_ms,
                message=message,
            )

        return _RawRunResult(
            verdict="OK",
            stdout=stdout,
            stderr=stderr,
            time_ms=elapsed_ms,
        )


def run_python3_once(code: str, stdin_text: str, *, time_limit_ms: int) -> RunResult:
    raw = _run_python3_once_raw(code, stdin_text, time_limit_ms=time_limit_ms)
    return RunResult(
        verdict=raw.verdict,
        stdout=_truncate(raw.stdout, STDIO_MAX_LEN),
        stderr=_truncate(raw.stderr, STDIO_MAX_LEN),
        time_ms=raw.time_ms,
        memory_kb=raw.memory_kb,
        message=raw.message,
    )


def judge_python3(code: str, testcases: list[Testcase], *, time_limit_ms: int) -> JudgeResult:
    """
    MVP local judge for Python3.
    - Runs user code with stdin = testcase.input_data
    - Compares stdout with expected_output after normalization
    """

    if not testcases:
        return JudgeResult(verdict="SE", message="No testcases configured")

    max_time_ms: int | None = None
    for idx, tc in enumerate(sorted(testcases, key=lambda t: t.sort_order), start=1):
        result = _run_python3_once_raw(code, tc.input_data or "", time_limit_ms=time_limit_ms)
        if result.time_ms is not None:
            max_time_ms = result.time_ms if max_time_ms is None else max(max_time_ms, result.time_ms)

        if result.verdict == "TLE":
            return JudgeResult(verdict="TLE", time_ms=time_limit_ms, message=f"TLE on testcase #{idx}")
        if result.verdict == "RE":
            return JudgeResult(verdict="RE", time_ms=max_time_ms, message=result.message or f"RE on testcase #{idx}")
        if result.verdict != "OK":
            return JudgeResult(verdict="SE", time_ms=max_time_ms, message=result.message or f"SE on testcase #{idx}")

        out = _norm(result.stdout)
        exp = _norm(tc.expected_output or "")
        if out != exp:
            return JudgeResult(verdict="WA", time_ms=max_time_ms, message=f"WA on testcase #{idx}")

    return JudgeResult(verdict="AC", time_ms=max_time_ms)
