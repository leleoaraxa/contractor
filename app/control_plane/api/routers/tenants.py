# app/control_plane/api/routers/tenants.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.control_plane.domain.tenants.repository import TenantAliasRepository
from app.control_plane.domain.tenants.service import TenantAliasService

router = APIRouter()

_repo = TenantAliasRepository()
_svc = TenantAliasService(_repo)


class SetCurrentRequest(BaseModel):
    bundle_id: str = Field(..., min_length=1)


@router.get("/tenants/{tenant_id}/aliases")
def get_aliases(tenant_id: str) -> dict:
    a = _svc.get_aliases(tenant_id)
    return {
        "tenant_id": a.tenant_id,
        "draft": a.draft_bundle_id,
        "candidate": a.candidate_bundle_id,
        "current": a.current_bundle_id,
    }


@router.post("/tenants/{tenant_id}/aliases/current")
def set_current(tenant_id: str, req: SetCurrentRequest) -> dict:
    a = _svc.set_current(tenant_id, req.bundle_id)
    return {
        "tenant_id": a.tenant_id,
        "current": a.current_bundle_id,
    }


@router.get("/tenants/{tenant_id}/resolve/{release_alias}")
def resolve_alias(tenant_id: str, release_alias: str) -> dict:
    if release_alias not in {"draft", "candidate", "current"}:
        raise HTTPException(status_code=400, detail="invalid release_alias")
    bundle_id = _svc.resolve(tenant_id, release_alias)
    if not bundle_id:
        raise HTTPException(status_code=404, detail="alias not set")
    return {
        "tenant_id": tenant_id,
        "release_alias": release_alias,
        "bundle_id": bundle_id,
    }
