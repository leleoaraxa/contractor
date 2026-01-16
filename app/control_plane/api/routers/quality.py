# app/control_plane/api/routers/quality.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.control_plane.api.routers import enforce_tenant_scope
from app.control_plane.domain.quality.service import QualityService
from app.shared.utils.ids import validate_tenant_id
from app.shared.errors import error_payload
from app.shared.security.auth import require_api_key
from app.shared.security.rate_limit import enforce_rate_limit

router = APIRouter()

_svc = QualityService()


@router.get("/tenants/{tenant_id}/bundles/{bundle_id}/quality")
def get_quality_report(tenant_id: str, bundle_id: str, request: Request) -> dict:
    validate_tenant_id(tenant_id)
    identity = require_api_key(request)
    enforce_tenant_scope(tenant_id, identity)
    enforce_rate_limit(tenant_id, "control.quality.report")
    try:
        return _svc.get_report(tenant_id, bundle_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=error_payload(
                error="quality_report_not_found",
                type="not_found",
                message="quality report not found",
            ),
        )


@router.post("/tenants/{tenant_id}/bundles/{bundle_id}/quality/run")
def run_quality_report(tenant_id: str, bundle_id: str, request: Request) -> dict:
    validate_tenant_id(tenant_id)
    identity = require_api_key(request)
    enforce_tenant_scope(tenant_id, identity)
    enforce_rate_limit(tenant_id, "control.quality.run")
    try:
        return _svc.run_quality(tenant_id, bundle_id)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=error_payload(
                error="bundle_not_found",
                type="not_found",
                message=str(e),
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=error_payload(
                error="validation_error",
                type="validation_error",
                message=str(e),
            ),
        )
