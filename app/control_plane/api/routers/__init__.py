# app/control_plane/api/routers/__init__.py
from __future__ import annotations

import os

from fastapi import HTTPException

from app.shared.config.settings import settings
from app.shared.errors import error_payload
from app.shared.security.auth import ApiKeyIdentity


def enforce_tenant_scope(tenant_id: str, identity: ApiKeyIdentity | None) -> None:
    if identity is None:
        return
    tenant_scope = (
        getattr(identity, "tenant_scope", None)
        or getattr(identity, "tenant_id", None)
        or getattr(identity, "tenant_ref", None)
    )
    if not tenant_scope:
        key = getattr(identity, "key", None)
        if key:
            configured = getattr(settings, "contractor_api_keys", None)
            if configured is None:
                configured = getattr(settings, "contractor_api_key", None)
            if isinstance(configured, str):
                entries = [value.strip() for value in configured.split(",") if value.strip()]
            elif isinstance(configured, (list, tuple, set)):
                entries = [str(value).strip() for value in configured if str(value).strip()]
            else:
                raw_keys = os.environ.get("CONTRACTOR_API_KEYS", "")
                entries = [value.strip() for value in raw_keys.split(",") if value.strip()]
            for entry in entries:
                parts = entry.split(":")
                if len(parts) < 3:
                    continue
                candidate_key = ":".join(parts[2:])
                if candidate_key == key:
                    tenant_scope = parts[0]
                    break
            if not tenant_scope:
                raw_keys = os.environ.get("CONTRACTOR_API_KEYS", "")
                for entry in [value.strip() for value in raw_keys.split(",") if value.strip()]:
                    parts = entry.split(":")
                    if len(parts) < 3:
                        continue
                    candidate_key = ":".join(parts[2:])
                    if candidate_key == key:
                        tenant_scope = parts[0]
                        break
    if not tenant_scope:
        raise HTTPException(
            status_code=403,
            detail=error_payload(
                error="tenant_scope_required",
                type="auth",
                message="tenant scope required",
            ),
        )
    if str(tenant_scope) != str(tenant_id):
        raise HTTPException(
            status_code=403,
            detail=error_payload(
                error="tenant_scope_mismatch",
                type="auth",
                message="tenant scope mismatch",
            ),
        )
