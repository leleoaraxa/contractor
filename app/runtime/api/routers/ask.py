# app/runtime/api/routers/ask.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.runtime.engine.context.artifact_loader import (
    ArtifactLoader,
    ArtifactLoaderError,
)
from app.runtime.engine.context.tenant_context import TenantContext
from app.runtime.engine.context.control_plane_client import ControlPlaneClient


router = APIRouter()


class AskRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1, pattern=r"^[A-Za-z0-9._-]+$")
    question: str = Field(..., min_length=1)
    conversation_id: str | None = None
    client_id: str | None = None

    # Stage 0+: allow explicit bundle_id OR release_alias resolution (default current)
    bundle_id: str | None = None
    release_alias: str = Field(default="current", pattern="^(draft|candidate|current)$")


class AskResponse(BaseModel):
    answer: str
    meta: dict


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    # Resolve bundle_id deterministically
    bundle_id = req.bundle_id
    if not bundle_id:
        cp = ControlPlaneClient()
        bundle_id = cp.resolve_bundle_id(req.tenant_id, req.release_alias)
        if not bundle_id:
            raise HTTPException(
                status_code=404, detail="bundle_id not provided and alias not set"
            )

    loader = ArtifactLoader()
    try:
        manifest = loader.load_manifest(req.tenant_id, bundle_id)
    except ArtifactLoaderError as e:
        raise HTTPException(status_code=404, detail=str(e))

    ctx = TenantContext(tenant_id=req.tenant_id, bundle_id=bundle_id)

    answer = (
        "CONTRACTOR runtime is up. Planner/Builder/Executor/Formatter are not implemented yet.\n"
        f"Received question: {req.question}"
    )

    meta = {
        "tenant_id": ctx.tenant_id,
        "bundle_id": ctx.bundle_id,
        "release_alias": req.release_alias if not req.bundle_id else None,
        "manifest": {
            "created_at": manifest.get("created_at"),
            "source": manifest.get("source"),
            "checksum": manifest.get("checksum"),
        },
        "decision": {
            "intent": None,
            "entity": None,
            "explain": {
                "stage": "foundation",
                "note": "decision is not implemented in Stage 0",
            },
        },
    }
    return AskResponse(answer=answer, meta=meta)
