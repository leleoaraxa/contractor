# app/control_plane/api/routers/quality.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.control_plane.domain.quality.service import QualityService
from app.shared.utils.ids import validate_tenant_id

router = APIRouter()

_svc = QualityService()


@router.get("/tenants/{tenant_id}/bundles/{bundle_id}/quality")
def get_quality_report(tenant_id: str, bundle_id: str) -> dict:
    validate_tenant_id(tenant_id)
    try:
        return _svc.get_report(tenant_id, bundle_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="quality report not found")


@router.post("/tenants/{tenant_id}/bundles/{bundle_id}/quality/run")
def run_quality_report(tenant_id: str, bundle_id: str) -> dict:
    validate_tenant_id(tenant_id)
    try:
        return _svc.run_quality(tenant_id, bundle_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
