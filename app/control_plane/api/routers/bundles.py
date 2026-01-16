# app/control_plane/api/routers/bundles.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.control_plane.api.routers import enforce_tenant_scope
from app.shared.utils.ids import validate_tenant_id
from app.control_plane.domain.bundles.validator import (
    ManifestNotFoundError,
    validate_bundle as validate_bundle_domain,
)
from app.shared.errors import error_payload
from app.shared.security.auth import require_api_key
from app.shared.security.rate_limit import enforce_rate_limit

router = APIRouter()


@router.get("/tenants/{tenant_id}/bundles/{bundle_id}/validate")
def validate_bundle(tenant_id: str, bundle_id: str, request: Request) -> dict:
    validate_tenant_id(tenant_id)
    identity = require_api_key(request)
    enforce_tenant_scope(tenant_id, identity)
    enforce_rate_limit(tenant_id, "control.validate_bundle")
    try:
        return validate_bundle_domain(tenant_id, bundle_id)
    except ManifestNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=error_payload(
                error="manifest_not_found",
                type="not_found",
                message=str(e),
            ),
        )
