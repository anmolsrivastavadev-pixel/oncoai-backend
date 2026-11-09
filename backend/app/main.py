"""FastAPI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool

from app.api.v1 import (
    appointments,
    assistant,
    auth,
    community,
    dermatologists,
    lesions,
    moderation,
    reminders,
    scans,
    tracking,
    users,
)
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.db.session import SessionLocal
from app.ml import registry
from app.services.seed import seed_dermatologists

logger = logging.getLogger(__name__)


def _startup() -> None:
    if settings.SEED_SAMPLE_DATA:
        try:
            with SessionLocal() as db:
                seed_dermatologists(db)
        except Exception:
            logger.exception("seeding sample data failed (have migrations been applied?)")
    if settings.MODEL_WARMUP:
        registry.warmup()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await run_in_threadpool(_startup)
    yield


def create_app() -> FastAPI:
    configure_logging(settings.LOG_LEVEL, settings.LOG_JSON)
    is_prod = settings.ENVIRONMENT == "production"
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        lifespan=lifespan,
        docs_url=None if is_prod else "/docs",
        redoc_url=None,
        openapi_url=None if is_prod else "/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID", "Retry-After"],
        max_age=600,
    )
    app.add_middleware(RequestContextMiddleware, hsts=is_prod)

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled error", exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.get("/health", tags=["health"])
    def health() -> dict[str, object]:
        db_status = "ok"
        try:
            with SessionLocal() as db:
                db.execute(text("SELECT 1"))
        except Exception:
            logger.exception("health check: database unavailable")
            db_status = "error"
        info = registry.get_analyzer().info
        return {
            "status": "ok" if db_status == "ok" else "degraded",
            "db": db_status,
            "model": {"loaded": info.loaded, "name": info.name, "kind": info.kind},
        }

    for module in (
        auth, users, lesions, scans, tracking, dermatologists, appointments, reminders,
        community, moderation, assistant,
    ):
        app.include_router(module.router, prefix=settings.API_V1_PREFIX)
    return app


app = create_app()
