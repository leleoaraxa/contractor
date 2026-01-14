# app/runtime/api/routers/healthz.py
from __future__ import annotations

from fastapi import APIRouter

from app.runtime.engine.runtime_identity import get_runtime_identity

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict:
    identity = get_runtime_identity()
    return {
        "status": "ok",
        "component": "runtime",
        "runtime_mode": identity.runtime_mode,
        "tenant_scope": identity.tenant_scope,
    }
