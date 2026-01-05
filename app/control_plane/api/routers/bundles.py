# app/control_plane/api/routers/bundles.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.shared.utils.ids import validate_tenant_id
from app.control_plane.domain.bundles.validator import (
    ManifestNotFoundError,
    validate_bundle as validate_bundle_domain,
)

router = APIRouter()

@router.get("/tenants/{tenant_id}/bundles/{bundle_id}/validate")
def validate_bundle(tenant_id: str, bundle_id: str) -> dict:
    validate_tenant_id(tenant_id)
    try:
        return validate_bundle_domain(tenant_id, bundle_id)
    except ManifestNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
