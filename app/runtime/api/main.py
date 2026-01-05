# app/runtime/api/main.py
from __future__ import annotations

from fastapi import FastAPI

from app.shared.logging.logger import configure_logging
from app.runtime.api.routers.healthz import router as healthz_router
from app.runtime.api.routers.ask import router as ask_router


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="CONTRACTOR Runtime", version="v1")

    app.include_router(healthz_router, prefix="/api/v1/runtime")
    app.include_router(ask_router, prefix="/api/v1/runtime")

    return app


app = create_app()
