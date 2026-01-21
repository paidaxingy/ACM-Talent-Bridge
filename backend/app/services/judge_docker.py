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


@dataclass(frozen=True)
class JudgeResult:
    verdict: str  # AC/WA/CE/RE/TLE/SE
    time_ms: int | None = None
    memory_kb: int | None = None
    message: str | None = None


def _norm(s: str) -> str:
    lines = [line.rstrip() for line in s.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _safe_read(path: Path, max_len: int = 4000) -> str:
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 (MVP)
        return ""
    return text[:max_len]


def _safe_decode_bytes(b: object, max_len: int = 4000) -> str:
    """
    docker SDK may attach stdout/stderr to ContainerError as bytes.
    We decode best-effort for debugging purposes.
    """
    if not b:
        return ""
    if isinstance(b, (bytes, bytearray)):
        try:
            return bytes(b).decode("utf-8", errors="replace")[:max_len]
        except Exception:  # noqa: BLE001 (MVP)
            return ""
    if isinstance(b, str):
        return b[:max_len]
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
    # If command exits non-zero, docker SDK raises ContainerError.
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


def judge_in_docker(
    *,
    code: str,
    language: str,
    testcases: list[Testcase],
    time_limit_ms: int,
    memory_limit_mb: int,
    settings: Settings,
) -> JudgeResult:
    """
    Docker sandbox judge (MVP implementation).

    Notes:
    - Uses a runner image containing `bash`, `timeout`, and language toolchain.
    - For docker-compose worker-in-container, prefer `judge_docker_mode=volume`
      and mount the volume into the worker at `judge_workspace_dir`.
    """

    if not testcases:
        return JudgeResult(verdict="SE", message="No testcases configured")

    lang = language
    if lang not in {"python3", "cpp17"}:
        return JudgeResult(verdict="CE", message=f"Unsupported language: {lang}")

    workspace = Path(settings.judge_workspace_dir)
    run_id = f"run_{uuid.uuid4().hex}"
    run_dir = workspace / run_id
    logger.info(f"Creating run directory: {run_dir}, workspace: {workspace}")
    run_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Run directory created: {run_dir.exists()}")

    # Map into runner container
    if settings.judge_docker_mode == "bind":
        volumes = {str(run_dir): {"bind": "/workspace", "mode": "rw"}}
        workdir = "/workspace"
        logger.info(f"Bind mode: host {run_dir} -> container /workspace")
    elif settings.judge_docker_mode == "volume":
        # worker must have the same docker volume mounted at `judge_workspace_dir`
        try:
            rel = run_dir.relative_to(workspace)
            logger.info(f"Volume mode: rel={rel}, run_dir={run_dir}, workspace={workspace}")
        except ValueError as e:
            # If run_dir is not under workspace, use the run_id directly
            logger.warning(f"run_dir not under workspace: {e}, using run_id={run_id}")
            rel = Path(run_id)
        volumes = {settings.judge_workspace_volume: {"bind": "/workspace", "mode": "rw"}}
        workdir = f"/workspace/{rel.as_posix()}"
        logger.info(f"Volume mode: volume={settings.judge_workspace_volume}, workdir={workdir}")
    else:
        shutil.rmtree(run_dir, ignore_errors=True)
        return JudgeResult(verdict="SE", message=f"Invalid JUDGE_DOCKER_MODE={settings.judge_docker_mode}")

    time_limit_s = max(1, int((time_limit_ms + 999) // 1000))
    mem_limit = f"{memory_limit_mb}m"

    try:
        # Use absolute paths inside runner container to avoid relying on `working_dir`
        # (some environments may not honor non-existent workdir immediately).
        in_dir = workdir
        input_in = f"{in_dir}/input.txt"
        output_out = f"{in_dir}/output.txt"
        stderr_out = f"{in_dir}/stderr.txt"

        if lang == "python3":
            (run_dir / "main.py").write_text(code, encoding="utf-8")
        else:
            (run_dir / "main.cpp").write_text(code, encoding="utf-8")
            # compile
            compile_cmd = f"cd {in_dir} && g++ -O2 -std=c++17 -pipe -o main main.cpp 2> {in_dir}/compile_err.txt"
            try:
                _run_container(
                    image=settings.judge_docker_image,
                    command=compile_cmd,
                    workdir=workdir,
                    volumes=volumes,
                    mem_limit=mem_limit,
                )
            except ContainerError as e:
                msg = _safe_read(run_dir / "compile_err.txt")
                if not msg:
                    msg = _safe_decode_bytes(getattr(e, "stderr", None)) or _safe_decode_bytes(getattr(e, "stdout", None))
                return JudgeResult(verdict="CE", message=msg or "Compile Error")

        max_time_ms: int = 0
        max_memory_kb: int | None = None

        for idx, tc in enumerate(sorted(testcases, key=lambda t: t.sort_order), start=1):
            input_file = run_dir / "input.txt"
            logger.info(f"Writing input to {input_file}, exists: {input_file.exists()}")
            input_file.write_text(tc.input_data or "", encoding="utf-8")
            logger.info(f"Input file written, size: {input_file.stat().st_size if input_file.exists() else 0}")
            # Clean previous outputs
            for fn in ("output.txt", "stderr.txt", "time.txt"):
                p = run_dir / fn
                if p.exists():
                    p.unlink()

            time_prefix = f"/usr/bin/time -f 'ELAPSED_SEC=%e\\nMAX_RSS_KB=%M' -o {in_dir}/time.txt "
            if lang == "python3":
                run_cmd = (
                    f"cd {in_dir} && "
                    f"{time_prefix}"
                    f"timeout -k 1s {time_limit_s}s python3 {in_dir}/main.py "
                    f"< {input_in} > {output_out} 2> {stderr_out}"
                )
            else:
                run_cmd = (
                    f"cd {in_dir} && "
                    f"{time_prefix}"
                    f"timeout -k 1s {time_limit_s}s {in_dir}/main "
                    f"< {input_in} > {output_out} 2> {stderr_out}"
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
                max_time_ms = max(max_time_ms, elapsed_ms)
            except ContainerError as e:
                if getattr(e, "exit_status", None) == 124:
                    return JudgeResult(verdict="TLE", time_ms=time_limit_ms, message=f"TLE on testcase #{idx}")
                msg = _safe_read(run_dir / "stderr.txt")
                if not msg:
                    msg = _safe_decode_bytes(getattr(e, "stderr", None)) or _safe_decode_bytes(getattr(e, "stdout", None))
                # Improve common misconfiguration hints (volume name / workspace mount mismatch).
                if msg and ("No such file or directory" in msg) and ("/workspace/run_" in msg or "/workspace/" in msg):
                    hint = (
                        "\n\n[hint] Docker 判题工作目录不存在。通常是 JUDGE_DOCKER_MODE=volume 时，"
                        "worker 写入的 volume 与 runner 挂载的 volume 不是同一个（例如 docker compose 自动给卷名加项目前缀）。"
                        f"\n[hint] 当前设置: JUDGE_DOCKER_MODE={settings.judge_docker_mode}, "
                        f"JUDGE_WORKSPACE_DIR={settings.judge_workspace_dir}, "
                        f"JUDGE_WORKSPACE_VOLUME={settings.judge_workspace_volume}"
                    )
                    msg = (msg + hint)[:4000]
                return JudgeResult(verdict="RE", message=msg or f"RE on testcase #{idx}")
            except DockerException as e:
                return JudgeResult(verdict="SE", message=str(e))

            metrics = _safe_read(run_dir / "time.txt", max_len=2000)
            if metrics:
                sec = None
                rss = None
                for line in metrics.splitlines():
                    line = line.strip()
                    if line.startswith("ELAPSED_SEC="):
                        try:
                            sec = float(line.split("=", 1)[1])
                        except Exception:  # noqa: BLE001
                            sec = None
                    elif line.startswith("MAX_RSS_KB="):
                        try:
                            rss = int(line.split("=", 1)[1])
                        except Exception:  # noqa: BLE001
                            rss = None
                if sec is not None:
                    max_time_ms = max(max_time_ms, int(sec * 1000))
                if rss is not None:
                    max_memory_kb = rss if max_memory_kb is None else max(max_memory_kb, rss)

            out = _norm(_safe_read(run_dir / "output.txt", max_len=200000))
            exp = _norm(tc.expected_output or "")
            if out != exp:
                return JudgeResult(verdict="WA", time_ms=max_time_ms or None, memory_kb=max_memory_kb, message=f"WA on testcase #{idx}")

        return JudgeResult(verdict="AC", time_ms=max_time_ms or None, memory_kb=max_memory_kb)
    except DockerException as e:
        return JudgeResult(verdict="SE", message=str(e))
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)

