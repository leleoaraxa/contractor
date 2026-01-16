# app/runtime/api/main.py
from __future__ import annotations

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

from app.shared.logging.logger import configure_logging
from app.shared.metrics import instrument_http
from app.shared.errors import register_exception_handlers
from app.runtime.api.routers.healthz import router as healthz_router
from app.runtime.api.routers.ask import router as ask_router


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="CONTRACTOR Runtime", version="v1")
    instrument_http(app, service="runtime")
    register_exception_handlers(app)

    app.include_router(healthz_router, prefix="/api/v1/runtime")
    app.include_router(ask_router, prefix="/api/v1/runtime")

    @app.get("/metrics")
    def metrics() -> Response:
        return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
