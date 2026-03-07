from __future__ import annotations

from app.core.config import get_settings
from app.services.judge_docker import RunResult, run_in_docker
from app.services.judge_local import run_python3_once


def run_code_once(*, code: str, language: str, stdin_text: str, time_limit_ms: int, memory_limit_mb: int) -> RunResult:
    settings = get_settings()

    if settings.judge_enable_docker:
        return run_in_docker(
            code=code,
            language=language,
            stdin_text=stdin_text,
            time_limit_ms=time_limit_ms,
            memory_limit_mb=memory_limit_mb,
            settings=settings,
        )

    if language != "python3":
        return RunResult(
            verdict="CE",
            message=f"Language not supported in local runner: {language}. Enable Docker runner for C++ 17.",
        )

    return run_python3_once(code, stdin_text, time_limit_ms=time_limit_ms)
