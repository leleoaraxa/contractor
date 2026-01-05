from __future__ import annotations

from fastapi import FastAPI

from app.shared.logging.logger import configure_logging
from app.control_plane.api.routers.healthz import router as healthz_router


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="CONTRACTOR Control Plane", version="v1")

    app.include_router(healthz_router, prefix="/api/v1/control")

    return app


app = create_app()
