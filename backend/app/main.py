from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Ensure DB is reachable and tables are ready (MVP: create_all)
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan,
    )

    # DEV-friendly CORS; will be tightened when frontend/auth is ready.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    resumes_dir = Path(settings.resumes_dir)
    resumes_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/resumes", StaticFiles(directory=str(resumes_dir)), name="resumes")

    return app


app = create_app()

