from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    app_name: str = "ACM-Talent-Bridge"
    env: str = "dev"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # DB
    database_url: str

    # Redis / Celery
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str
    celery_always_eager: bool = False
    celery_eager_propagates: bool = True

    # Security (MVP)
    jwt_secret: str = "change_me"
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 720

    # OJ/Judge
    judge_docker_image: str = "acm-judge-runner:latest"
    judge_time_limit_ms: int = 2000
    judge_memory_limit_mb: int = 256
    judge_enable_docker: bool = False
    # Docker runner mode:
    # - bind: bind-mount `judge_workspace_dir` (host path) into runner container (best for local dev)
    # - volume: mount docker volume `judge_workspace_volume` into runner container, and write files under
    #   `judge_workspace_dir` (which should be the same volume mounted into the worker container)
    judge_docker_mode: str = "bind"
    judge_workspace_dir: str = "/tmp/acm_judge"
    judge_workspace_volume: str = "judge_workspace"

    # AI
    ai_provider: str = "mock"
    ai_api_key: str | None = None
    ai_base_url: str | None = None
    ai_model: str = "gpt-4o-mini"

    # Resumes
    resumes_dir: str = "resumes"

    model_config = SettingsConfigDict(
        env_file=(".env",),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Load settings from env vars, optionally from an env file.

    - Default: load `.env` from current working directory (useful when `cd backend`)
    - Override: set `ENV_FILE=/abs/path/to/.env` to load a specific file
    """

    env_file = os.getenv("ENV_FILE")
    if env_file:
        return Settings(_env_file=env_file)
    return Settings()

