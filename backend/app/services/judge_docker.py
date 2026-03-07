from __future__ import annotations

import logging
import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import docker
from docker.errors import ContainerError, DockerException

from app.core.config import Settings
from app.models.problem import Testcase

logger = logging.getLogger(__name__)
STDIO_MAX_LEN = 20_000
COMPARE_STDOUT_MAX_LEN = 200_000
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
    verdict: str  # OK/CE/RE/TLE/SE
    stdout: str = ""
    stderr: str = ""
    time_ms: int | None = None
    memory_kb: int | None = None
    message: str | None = None


def _norm(s: str) -> str:
    lines = [line.rstrip() for line in s.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _safe_read(path: Path, max_len: int = MESSAGE_MAX_LEN) -> str:
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return ""
    return text[:max_len]


def _safe_decode_bytes(raw: object, max_len: int = MESSAGE_MAX_LEN) -> str:
    if not raw:
        return ""
    if isinstance(raw, (bytes, bytearray)):
        try:
            return bytes(raw).decode("utf-8", errors="replace")[:max_len]
        except Exception:  # noqa: BLE001
            return ""
    if isinstance(raw, str):
        return raw[:max_len]
    return ""


def _run_container(
    *,
    image: str,
    command: str,
    workdir: str,
    volumes: dict,
    mem_limit: str,
    network_disabled: bool = True,
    user: str = "0:0",
) -> None:
    client = docker.from_env()
    client.containers.run(
        image=image,
        command=["bash", "-lc", command],
        working_dir=workdir,
        volumes=volumes,
        network_disabled=network_disabled,
        mem_limit=mem_limit,
        user=user,
        pids_limit=128,
        cap_drop=["ALL"],
        security_opt=["no-new-privileges:true"],
        detach=False,
        remove=True,
        stdout=True,
        stderr=True,
    )


def _prepare_workspace(settings: Settings) -> tuple[Path, dict, str] | tuple[None, None, None]:
    workspace = Path(settings.judge_workspace_dir)
    run_id = f"run_{uuid.uuid4().hex}"
    run_dir = workspace / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    if settings.judge_docker_mode == "bind":
        volumes = {str(run_dir): {"bind": "/workspace", "mode": "rw"}}
        workdir = "/workspace"
        return run_dir, volumes, workdir

    if settings.judge_docker_mode == "volume":
        try:
            rel = run_dir.relative_to(workspace)
        except ValueError:
            rel = Path(run_id)
        volumes = {settings.judge_workspace_volume: {"bind": "/workspace", "mode": "rw"}}
        workdir = f"/workspace/{rel.as_posix()}"
        return run_dir, volumes, workdir

    shutil.rmtree(run_dir, ignore_errors=True)
    return None, None, None


def _parse_metrics(metrics: str) -> tuple[int | None, int | None]:
    elapsed_ms = None
    memory_kb = None
    for line in metrics.splitlines():
        line = line.strip()
        if line.startswith("ELAPSED_SEC="):
            try:
                elapsed_ms = int(float(line.split("=", 1)[1]) * 1000)
            except Exception:  # noqa: BLE001
                elapsed_ms = None
        elif line.startswith("MAX_RSS_KB="):
            try:
                memory_kb = int(line.split("=", 1)[1])
            except Exception:  # noqa: BLE001
                memory_kb = None
    return elapsed_ms, memory_kb


def _workspace_hint(message: str, settings: Settings) -> str:
    if "No such file or directory" not in message:
        return message
    if "/workspace/run_" not in message and "/workspace/" not in message:
        return message
    hint = (
        "\n\n[hint] Docker 判题工作目录不存在。通常是 JUDGE_DOCKER_MODE=volume 时，"
        "worker 写入的 volume 与 runner 挂载的 volume 不是同一个（例如 docker compose 自动给卷名加项目前缀）。"
        f"\n[hint] 当前设置: JUDGE_DOCKER_MODE={settings.judge_docker_mode}, "
        f"JUDGE_WORKSPACE_DIR={settings.judge_workspace_dir}, "
        f"JUDGE_WORKSPACE_VOLUME={settings.judge_workspace_volume}"
    )
    return (message + hint)[:MESSAGE_MAX_LEN]


def _compile_if_needed(
    *,
    code: str,
    language: str,
    run_dir: Path,
    workdir: str,
    volumes: dict,
    mem_limit: str,
    settings: Settings,
) -> RunResult | None:
    if language == "python3":
        (run_dir / "main.py").write_text(code, encoding="utf-8")
        return None

    (run_dir / "main.cpp").write_text(code, encoding="utf-8")
    compile_cmd = f"cd {workdir} && g++ -O2 -std=c++17 -pipe -o main main.cpp 2> {workdir}/compile_err.txt"
    try:
        _run_container(
            image=settings.judge_docker_image,
            command=compile_cmd,
            workdir=workdir,
            volumes=volumes,
            mem_limit=mem_limit,
        )
        return None
    except ContainerError as exc:
        message = _safe_read(run_dir / "compile_err.txt")
        if not message:
            message = _safe_decode_bytes(getattr(exc, "stderr", None)) or _safe_decode_bytes(getattr(exc, "stdout", None))
        message = message or "Compile Error"
        return RunResult(verdict="CE", stderr=message[:STDIO_MAX_LEN], message=message[:MESSAGE_MAX_LEN])
    except DockerException as exc:
        message = str(exc)
        return RunResult(verdict="SE", message=message[:MESSAGE_MAX_LEN], stderr=message[:STDIO_MAX_LEN])


def _run_once_raw(
    *,
    language: str,
    stdin_text: str,
    time_limit_ms: int,
    run_dir: Path,
    workdir: str,
    volumes: dict,
    mem_limit: str,
    settings: Settings,
) -> _RawRunResult:
    input_file = run_dir / "input.txt"
    input_file.write_text(stdin_text or "", encoding="utf-8")
    for filename in ("output.txt", "stderr.txt", "time.txt"):
        path = run_dir / filename
        if path.exists():
            path.unlink()

    time_limit_s = max(1, int((time_limit_ms + 999) // 1000))
    time_prefix = f"/usr/bin/time -f 'ELAPSED_SEC=%e\\nMAX_RSS_KB=%M' -o {workdir}/time.txt "
    if language == "python3":
        run_cmd = (
            f"cd {workdir} && "
            f"{time_prefix}"
            f"timeout -k 1s {time_limit_s}s python3 {workdir}/main.py "
            f"< {workdir}/input.txt > {workdir}/output.txt 2> {workdir}/stderr.txt"
        )
    else:
        run_cmd = (
            f"cd {workdir} && "
            f"{time_prefix}"
            f"timeout -k 1s {time_limit_s}s {workdir}/main "
            f"< {workdir}/input.txt > {workdir}/output.txt 2> {workdir}/stderr.txt"
        )

    try:
        start = time.perf_counter()
        _run_container(
            image=settings.judge_docker_image,
            command=run_cmd,
            workdir=workdir,
            volumes=volumes,
            mem_limit=mem_limit,
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
    except ContainerError as exc:
        stdout = _safe_read(run_dir / "output.txt", max_len=COMPARE_STDOUT_MAX_LEN)
        stderr = _safe_read(run_dir / "stderr.txt", max_len=STDIO_MAX_LEN)
        if getattr(exc, "exit_status", None) == 124:
            return _RawRunResult(
                verdict="TLE",
                stdout=stdout,
                stderr=stderr,
                time_ms=time_limit_ms,
                message="Execution timed out",
            )
        if not stderr:
            stderr = _safe_decode_bytes(getattr(exc, "stderr", None), max_len=STDIO_MAX_LEN)
            if not stderr:
                stderr = _safe_decode_bytes(getattr(exc, "stdout", None), max_len=STDIO_MAX_LEN)
        stderr = _workspace_hint(stderr, settings)
        message = stderr[:MESSAGE_MAX_LEN] or "Runtime Error"
        return _RawRunResult(
            verdict="RE",
            stdout=stdout,
            stderr=stderr,
            message=message,
        )
    except DockerException as exc:
        message = str(exc)
        return _RawRunResult(verdict="SE", stderr=message, message=message[:MESSAGE_MAX_LEN])

    metrics = _safe_read(run_dir / "time.txt", max_len=2000)
    parsed_time_ms, memory_kb = _parse_metrics(metrics) if metrics else (None, None)
    stdout = _safe_read(run_dir / "output.txt", max_len=STDIO_MAX_LEN)
    stderr = _safe_read(run_dir / "stderr.txt", max_len=STDIO_MAX_LEN)
    return _RawRunResult(
        verdict="OK",
        stdout=stdout,
        stderr=stderr,
        time_ms=parsed_time_ms if parsed_time_ms is not None else elapsed_ms,
        memory_kb=memory_kb,
    )


def run_in_docker(
    *,
    code: str,
    language: str,
    stdin_text: str,
    time_limit_ms: int,
    memory_limit_mb: int,
    settings: Settings,
) -> RunResult:
    if language not in {"python3", "cpp17"}:
        return RunResult(verdict="CE", message=f"Unsupported language: {language}")

    try:
        workspace = _prepare_workspace(settings)
    except OSError as exc:
        return RunResult(verdict="SE", message=f"Cannot prepare judge workspace: {exc}")

    run_dir, volumes, workdir = workspace
    if run_dir is None or volumes is None or workdir is None:
        return RunResult(verdict="SE", message=f"Invalid JUDGE_DOCKER_MODE={settings.judge_docker_mode}")

    mem_limit = f"{memory_limit_mb}m"
    try:
        compile_result = _compile_if_needed(
            code=code,
            language=language,
            run_dir=run_dir,
            workdir=workdir,
            volumes=volumes,
            mem_limit=mem_limit,
            settings=settings,
        )
        if compile_result is not None:
            return compile_result

        raw = _run_once_raw(
            language=language,
            stdin_text=stdin_text,
            time_limit_ms=time_limit_ms,
            run_dir=run_dir,
            workdir=workdir,
            volumes=volumes,
            mem_limit=mem_limit,
            settings=settings,
        )
        return RunResult(
            verdict=raw.verdict,
            stdout=raw.stdout[:STDIO_MAX_LEN],
            stderr=raw.stderr[:STDIO_MAX_LEN],
            time_ms=raw.time_ms,
            memory_kb=raw.memory_kb,
            message=raw.message,
        )
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def judge_in_docker(
    *,
    code: str,
    language: str,
    testcases: list[Testcase],
    time_limit_ms: int,
    memory_limit_mb: int,
    settings: Settings,
) -> JudgeResult:
    if not testcases:
        return JudgeResult(verdict="SE", message="No testcases configured")
    if language not in {"python3", "cpp17"}:
        return JudgeResult(verdict="CE", message=f"Unsupported language: {language}")

    try:
        workspace = _prepare_workspace(settings)
    except OSError as exc:
        return JudgeResult(verdict="SE", message=f"Cannot prepare judge workspace: {exc}")

    run_dir, volumes, workdir = workspace
    if run_dir is None or volumes is None or workdir is None:
        return JudgeResult(verdict="SE", message=f"Invalid JUDGE_DOCKER_MODE={settings.judge_docker_mode}")

    mem_limit = f"{memory_limit_mb}m"
    try:
        compile_result = _compile_if_needed(
            code=code,
            language=language,
            run_dir=run_dir,
            workdir=workdir,
            volumes=volumes,
            mem_limit=mem_limit,
            settings=settings,
        )
        if compile_result is not None:
            return JudgeResult(verdict=compile_result.verdict, message=compile_result.message)

        max_time_ms: int | None = None
        max_memory_kb: int | None = None
        for idx, tc in enumerate(sorted(testcases, key=lambda t: t.sort_order), start=1):
            result = _run_once_raw(
                language=language,
                stdin_text=tc.input_data or "",
                time_limit_ms=time_limit_ms,
                run_dir=run_dir,
                workdir=workdir,
                volumes=volumes,
                mem_limit=mem_limit,
                settings=settings,
            )

            if result.time_ms is not None:
                max_time_ms = result.time_ms if max_time_ms is None else max(max_time_ms, result.time_ms)
            if result.memory_kb is not None:
                max_memory_kb = result.memory_kb if max_memory_kb is None else max(max_memory_kb, result.memory_kb)

            if result.verdict == "TLE":
                return JudgeResult(verdict="TLE", time_ms=time_limit_ms, memory_kb=max_memory_kb, message=f"TLE on testcase #{idx}")
            if result.verdict in {"RE", "SE", "CE"}:
                return JudgeResult(
                    verdict=result.verdict,
                    time_ms=max_time_ms,
                    memory_kb=max_memory_kb,
                    message=result.message or f"{result.verdict} on testcase #{idx}",
                )

            out = _norm(result.stdout)
            exp = _norm(tc.expected_output or "")
            if out != exp:
                return JudgeResult(
                    verdict="WA",
                    time_ms=max_time_ms,
                    memory_kb=max_memory_kb,
                    message=f"WA on testcase #{idx}",
                )

        return JudgeResult(verdict="AC", time_ms=max_time_ms, memory_kb=max_memory_kb)
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)
