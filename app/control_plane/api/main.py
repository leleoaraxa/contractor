# app/control_plane/api/main.py
from __future__ import annotations

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

from app.shared.logging.logger import configure_logging
from app.shared.metrics import instrument_http
from app.shared.errors import register_exception_handlers
from app.control_plane.api.routers.healthz import router as healthz_router
from app.control_plane.api.routers.tenants import router as tenants_router
from app.control_plane.api.routers.bundles import router as bundles_router
from app.control_plane.api.routers.quality import router as quality_router
from app.control_plane.api.routers.versions import router as versions_router


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(title="CONTRACTOR Control Plane", version="v1")
    instrument_http(app, service="control")
    register_exception_handlers(app)

    app.include_router(healthz_router, prefix="/api/v1/control")
    app.include_router(tenants_router, prefix="/api/v1/control")
    app.include_router(bundles_router, prefix="/api/v1/control")
    app.include_router(quality_router, prefix="/api/v1/control")
    app.include_router(versions_router, prefix="/api/v1/control")

    @app.get("/metrics")
    def metrics() -> Response:
        return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)

    return app


app = create_app()
