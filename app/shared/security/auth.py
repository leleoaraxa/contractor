# app/shared/security/auth.py
from __future__ import annotations

from dataclasses import dataclass
import importlib

from fastapi import HTTPException, Request, status

from app.shared.errors import error_payload

def _get_settings():
    settings_module = importlib.import_module("app.shared.config.settings")
    return settings_module.settings


@dataclass(frozen=True)
class ApiKeyIdentity:
    key: str
    tenant_id: str | None
    role: str | None


def _parse_key_entry(entry: str) -> ApiKeyIdentity:
    parts = [part.strip() for part in str(entry).split(":") if part.strip()]
    if not parts:
        return ApiKeyIdentity(key="", tenant_id=None, role=None)
    if len(parts) == 1:
        return ApiKeyIdentity(key=parts[0], tenant_id=None, role=None)
    if len(parts) == 2:
        return ApiKeyIdentity(key=parts[1], tenant_id=parts[0], role=None)
    return ApiKeyIdentity(key=":".join(parts[2:]), tenant_id=parts[0], role=parts[1])


def _normalized_keys() -> list[ApiKeyIdentity]:
    raw = _get_settings().contractor_api_keys or []
    identities: list[ApiKeyIdentity] = []
    for entry in raw:
        parsed = _parse_key_entry(entry)
        if parsed.key:
            identities.append(parsed)
    return identities


def _has_tenant_scoped_keys() -> bool:
    return any(identity.tenant_id for identity in _normalized_keys())


def auth_disabled() -> bool:
    return bool(_get_settings().contractor_auth_disabled)


def require_api_key(request: Request) -> ApiKeyIdentity | None:
    if auth_disabled():
        return None

    allowed_identities = _normalized_keys()
    if not allowed_identities:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_payload(
                error="auth_required",
                type="auth",
                message="authentication required: configure CONTRACTOR_API_KEYS",
            ),
        )

    provided = (request.headers.get("X-API-Key") or "").strip()
    if not provided:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_payload(
                error="missing_api_key",
                type="auth",
                message="missing X-API-Key",
            ),
        )

    matched = next(
        (identity for identity in allowed_identities if identity.key == provided), None
    )
    if not matched:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_payload(
                error="invalid_api_key",
                type="auth",
                message="invalid API key",
            ),
        )
    return matched


def enforce_tenant_scope(
    identity: ApiKeyIdentity | None,
    tenant_id: str,
    *,
    allowed_roles: set[str] | None = None,
) -> None:
    if identity is None:
        return
    if allowed_roles:
        if identity.tenant_id is None:
            if not _has_tenant_scoped_keys():
                return
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_payload(
                    error="tenant_scope_required",
                    type="auth",
                    message="tenant scope required",
                ),
            )
        if identity.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_payload(
                    error="tenant_scope_mismatch",
                    type="auth",
                    message="tenant scope mismatch",
                ),
            )
        if identity.role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_payload(
                    error="identity_role_required",
                    type="auth",
                    message="identity role required",
                ),
            )
        if identity.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_payload(
                    error="identity_role_not_allowed",
                    type="auth",
                    message="identity role not allowed",
                ),
            )
        return
    if identity.tenant_id and identity.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_payload(
                error="tenant_scope_mismatch",
                type="auth",
                message="tenant scope mismatch",
            ),
        )


def outbound_auth_headers() -> dict[str, str]:
    if auth_disabled():
        return {}

    allowed_identities = _normalized_keys()
    if not allowed_identities:
        return {}
    # deterministic selection of the first key
    identity = sorted(allowed_identities, key=lambda item: item.key)[0]
    return {"X-API-Key": identity.key}
