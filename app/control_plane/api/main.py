# app/control_plane/api/main.py
from __future__ import annotations

from fastapi import FastAPI

from app.shared.logging.logger import configure_logging
from app.control_plane.api.routers.healthz import router as healthz_router
from app.control_plane.api.routers.tenants import router as tenants_router
from app.control_plane.api.routers.bundles import router as bundles_router


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="CONTRACTOR Control Plane", version="v1")

    app.include_router(healthz_router, prefix="/api/v1/control")
    app.include_router(tenants_router, prefix="/api/v1/control")
    app.include_router(bundles_router, prefix="/api/v1/control")

    return app


app = create_app()
