# app/control_plane/api/routers/versions.py
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.control_plane.api.routers import enforce_tenant_scope
from app.control_plane.domain.bundles.promoter import Alias
from app.control_plane.domain.quality.service import PromotionGateError
from app.control_plane.domain.tenants.repository import TenantAliasRepository
from app.control_plane.domain.tenants.service import TenantAliasService
from app.shared.security.auth import require_api_key
from app.shared.security.rate_limit import enforce_rate_limit
from app.shared.utils.ids import validate_tenant_id
from app.shared.errors import error_payload

router = APIRouter()
_repo = TenantAliasRepository()
_svc = TenantAliasService(_repo)


class VersionSetPayload(BaseModel):
    bundle_id: str = Field(..., min_length=1)


class VersionResponse(BaseModel):
    aliases: dict[Alias, Optional[str]]


@router.get(
    "/tenants/{tenant_id}/versions",
    response_model=VersionResponse,
    summary="Get all aliases for a tenant",
)
def get_aliases(tenant_id: str, request: Request) -> VersionResponse:
    validate_tenant_id(tenant_id)
    identity = require_api_key(request)
    enforce_tenant_scope(tenant_id, identity)
    enforce_rate_limit(tenant_id, "control.get_aliases")

    aliases = _svc.get_aliases(tenant_id)
    return VersionResponse(
        aliases={
            "draft": aliases.draft_bundle_id,
            "candidate": aliases.candidate_bundle_id,
            "current": aliases.current_bundle_id,
        }
    )


@router.put(
    "/tenants/{tenant_id}/versions/{alias}",
    response_model=VersionResponse,
    summary="Set an alias for a tenant",
)
def set_alias(
    tenant_id: str, alias: Alias, payload: VersionSetPayload, request: Request
) -> VersionResponse:
    validate_tenant_id(tenant_id)
    identity = require_api_key(request)
    enforce_tenant_scope(tenant_id, identity)
    enforce_rate_limit(tenant_id, "control.set_alias")

    try:
        if alias == "current":
            aliases = _svc.set_current(tenant_id, payload.bundle_id, actor=identity)
        elif alias == "candidate":
            aliases = _svc.set_candidate(tenant_id, payload.bundle_id, actor=identity)
        else:
            aliases = _svc.set_draft(tenant_id, payload.bundle_id, actor=identity)
    except PromotionGateError as e:
        raise HTTPException(status_code=400, detail=_svc.format_gate_error(e))
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=error_payload(
                error="validation_error",
                type="validation_error",
                message=str(e),
            ),
        )

    return VersionResponse(
        aliases={
            "draft": aliases.draft_bundle_id,
            "candidate": aliases.candidate_bundle_id,
            "current": aliases.current_bundle_id,
        }
    )


@router.get(
    "/tenants/{tenant_id}/versions/{alias}/resolve",
    summary="Resolve an alias to a bundle_id",
)
def resolve_alias(tenant_id: str, alias: Alias, request: Request) -> dict:
    validate_tenant_id(tenant_id)
    # This is a public-facing endpoint for the runtime client, so no API key is required
    # require_api_key(request)
    enforce_rate_limit(tenant_id, "control.resolve_alias")

    try:
        bundle_id = _svc.resolve(tenant_id, alias)
        if not bundle_id:
            raise HTTPException(
                status_code=404,
                detail=error_payload(
                    error="alias_not_set",
                    type="not_found",
                    message="alias not set",
                ),
            )
        return {"tenant_id": tenant_id, "alias": alias, "bundle_id": bundle_id}
    except HTTPException:
        raise
