# app/shared/security/auth.py
from __future__ import annotations

from dataclasses import dataclass
import importlib
import os

from fastapi import HTTPException, Request, status

from app.shared.config.settings import _normalize_api_keys

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
    raw_settings = list(_get_settings().contractor_api_keys or [])
    raw_env = os.environ.get("CONTRACTOR_API_KEYS")
    if raw_env is None:
        raw_env = os.environ.get("CONTRACTOR_API_KEY")
    raw_env_list = _normalize_api_keys(raw_env) if raw_env is not None else []
    # Prefer ENV keys over SETTINGS keys for deterministic precedence.
    raw = [*raw_env_list, *raw_settings]
    identities: list[ApiKeyIdentity] = []
    seen: set[tuple[str, str | None, str | None]] = set()
    for entry in raw:
        parsed = _parse_key_entry(entry)
        if not parsed.key:
            continue
        identity_key = (parsed.key, parsed.tenant_id, parsed.role)
        if identity_key in seen:
            continue
        seen.add(identity_key)
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
            detail="authentication required: configure CONTRACTOR_API_KEYS",
        )

    provided = (request.headers.get("X-API-Key") or "").strip()
    if not provided:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing X-API-Key",
        )

    matches = [identity for identity in allowed_identities if identity.key == provided]
    matched = next((identity for identity in matches if identity.tenant_id), None)
    if not matched and matches:
        matched = matches[0]
    if not matched:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="invalid API key",
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
                detail="tenant scope required",
            )
        if identity.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="tenant scope mismatch",
            )
        if identity.role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="identity role required",
            )
        if identity.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="identity role not allowed",
            )
        return
    if identity.tenant_id and identity.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="tenant scope mismatch",
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
