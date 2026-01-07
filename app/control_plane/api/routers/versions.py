# app/control_plane/api/routers/versions.py
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.control_plane.domain.bundles.promoter import (
    Alias,
    AliasNotFoundError,
    Promoter,
)
from app.shared.security.auth import require_api_key
from app.shared.security.rate_limit import enforce_rate_limit
from app.shared.utils.ids import validate_tenant_id

router = APIRouter()


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
    require_api_key(request)
    enforce_rate_limit(tenant_id, "control.get_aliases")

    promoter = Promoter()
    aliases = promoter.get_aliases_for_tenant(tenant_id)
    return VersionResponse(aliases=aliases)


@router.put(
    "/tenants/{tenant_id}/versions/{alias}",
    response_model=VersionResponse,
    summary="Set an alias for a tenant",
)
def set_alias(
    tenant_id: str, alias: Alias, payload: VersionSetPayload, request: Request
) -> VersionResponse:
    validate_tenant_id(tenant_id)
    require_api_key(request)
    enforce_rate_limit(tenant_id, "control.set_alias")

    promoter = Promoter()
    aliases = promoter.set_alias(tenant_id, payload.bundle_id, alias)
    return VersionResponse(aliases=aliases)


@router.get(
    "/tenants/{tenant_id}/versions/{alias}/resolve",
    summary="Resolve an alias to a bundle_id",
)
def resolve_alias(tenant_id: str, alias: Alias, request: Request) -> dict:
    validate_tenant_id(tenant_id)
    # This is a public-facing endpoint for the runtime client, so no API key is required
    # require_api_key(request)
    enforce_rate_limit(tenant_id, "control.resolve_alias")

    promoter = Promoter()
    try:
        bundle_id = promoter.get_alias(tenant_id, alias)
        return {"tenant_id": tenant_id, "alias": alias, "bundle_id": bundle_id}
    except AliasNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
