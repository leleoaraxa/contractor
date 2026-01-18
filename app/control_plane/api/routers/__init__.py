# app/control_plane/api/routers/__init__.py
from __future__ import annotations

from fastapi import HTTPException

from app.shared.errors import error_payload
from app.shared.security.auth import ApiKeyIdentity


def enforce_tenant_scope(tenant_id: str, identity: ApiKeyIdentity | None) -> None:
    if identity is None:
        return
    tenant_scope = (
        getattr(identity, "tenant_id", None)
        or getattr(identity, "tenant_scope", None)
        or getattr(identity, "tenant_ref", None)
    )
    if not tenant_scope:
        raise HTTPException(
            status_code=403,
            detail=error_payload(
                error="tenant_scope_required",
                type="auth_error",
                message="tenant scope required",
                details={"tenant_id": tenant_id, "tenant_scope": tenant_scope},
            ),
        )
    if str(tenant_scope) != str(tenant_id):
        raise HTTPException(
            status_code=403,
            detail=error_payload(
                error="tenant_scope_mismatch",
                type="auth_error",
                message="tenant scope mismatch",
                details={"tenant_id": tenant_id, "tenant_scope": tenant_scope},
            ),
        )
