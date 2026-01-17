# app/control_plane/api/routers/__init__.py
from __future__ import annotations

from fastapi import HTTPException

from app.shared.security.auth import ApiKeyIdentity


def enforce_tenant_scope(tenant_id: str, identity: ApiKeyIdentity | None) -> None:
    if identity is None:
        return
    tenant_scope = getattr(identity, "tenant_id", None)
    if not tenant_scope:
        raise HTTPException(status_code=403, detail="tenant scope required")
    if str(tenant_scope) != str(tenant_id):
        raise HTTPException(status_code=403, detail="tenant scope mismatch")
