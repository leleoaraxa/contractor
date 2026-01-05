from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.runtime.engine.context.artifact_loader import (
    ArtifactLoader,
    ArtifactLoaderError,
)
from app.runtime.engine.context.tenant_context import TenantContext


router = APIRouter()


class AskRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1)
    conversation_id: str | None = None
    client_id: str | None = None
    bundle_id: str = Field(
        ..., min_length=1
    )  # Stage 0 explicit; later resolve alias current/candidate.


class AskResponse(BaseModel):
    answer: str
    meta: dict


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    loader = ArtifactLoader()
    try:
        manifest = loader.load_manifest(req.tenant_id, req.bundle_id)
    except ArtifactLoaderError as e:
        raise HTTPException(status_code=404, detail=str(e))

    ctx = TenantContext(tenant_id=req.tenant_id, bundle_id=req.bundle_id)

    # Stage 0: deterministic stub (no domain logic).
    answer = (
        "CONTRACTOR runtime is up. Planner/Builder/Executor/Formatter are not implemented yet.\n"
        f"Received question: {req.question}"
    )

    meta = {
        "tenant_id": ctx.tenant_id,
        "bundle_id": ctx.bundle_id,
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
