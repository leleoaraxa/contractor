from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, Header, HTTPException, status

from app.audit import AuditConfigError, audit_emit, now_utc_iso

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALIAS_PATH = REPO_ROOT / "data" / "control_plane" / "demo_aliases.json"
DEFAULT_TENANT_AUTH_PATH = REPO_ROOT / "data" / "control_plane" / "tenants.json"

AUTH_CONFIG_PATH_ENV = "CONTRACTOR_CONTROL_PLANE_TENANT_AUTH_CONFIG_PATH"
AUTH_CONFIG_JSON_ENV = "CONTRACTOR_CONTROL_PLANE_TENANT_AUTH_CONFIG_JSON"
ALIAS_CONFIG_PATH_ENV = "CONTRACTOR_CONTROL_PLANE_ALIAS_CONFIG_PATH"

app = FastAPI()


class AuthConfigError(RuntimeError):
    """Raised when tenant auth configuration is unavailable or invalid."""


def _load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml_file(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_alias_config() -> dict[str, Any]:
    env_path = os.getenv(ALIAS_CONFIG_PATH_ENV)
    alias_path = Path(env_path) if env_path else DEFAULT_ALIAS_PATH
    try:
        return _load_json_file(alias_path)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _load_tenant_auth_config_payload() -> dict[str, Any]:
    env_json = os.getenv(AUTH_CONFIG_JSON_ENV)
    if env_json:
        try:
            return json.loads(env_json)
        except json.JSONDecodeError as exc:
            raise AuthConfigError("Invalid tenant auth config JSON in environment") from exc

    env_path = os.getenv(AUTH_CONFIG_PATH_ENV)
    auth_path = Path(env_path) if env_path else DEFAULT_TENANT_AUTH_PATH
    try:
        return _load_json_file(auth_path)
    except FileNotFoundError as exc:
        raise AuthConfigError("Tenant auth config file is missing") from exc
    except json.JSONDecodeError as exc:
        raise AuthConfigError("Tenant auth config file has invalid JSON") from exc


def load_tenant_token_index() -> dict[str, str]:
    config = _load_tenant_auth_config_payload()
    tenants = config.get("tenants") if isinstance(config, dict) else None
    if not isinstance(tenants, dict) or not tenants:
        raise AuthConfigError("Tenant auth config must define a non-empty tenants object")

    token_to_tenant: dict[str, str] = {}
    for tenant_id, tenant_cfg in tenants.items():
        if not isinstance(tenant_id, str) or not tenant_id:
            raise AuthConfigError("Tenant auth config has invalid tenant_id")
        if not isinstance(tenant_cfg, dict):
            raise AuthConfigError("Tenant auth config tenant entry must be an object")
        token = tenant_cfg.get("token")
        if not isinstance(token, str) or not token:
            raise AuthConfigError("Tenant auth config token must be a non-empty string")
        if token in token_to_tenant:
            raise AuthConfigError("Tenant auth config token must map to exactly one tenant")
        token_to_tenant[token] = tenant_id

    return token_to_tenant


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization",
        )
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0] != "Bearer" or not parts[1]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed Authorization",
        )
    return parts[1]


def enforce_control_plane_auth(
    tenant_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
) -> str:
    token = _extract_bearer_token(authorization)
    if not x_tenant_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Tenant-Id")

    try:
        token_to_tenant = load_tenant_token_index()
    except AuthConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    token_tenant_id = token_to_tenant.get(token)
    if token_tenant_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if token_tenant_id != x_tenant_id or tenant_id != x_tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return token_tenant_id


def resolve_current_bundle_metadata(tenant_id: str) -> tuple[str, str, str | None]:
    config = load_alias_config()
    tenants = config.get("tenants", config)
    tenant_entry = tenants.get(tenant_id) or tenants.get("*")
    if not tenant_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    bundle_sha256: str | None = None
    if isinstance(tenant_entry, str):
        bundle_path_value = tenant_entry
        bundle_id = None
    else:
        bundle_path_value = tenant_entry.get("current_bundle_path") or tenant_entry.get(
            "bundle_path"
        )
        bundle_id = tenant_entry.get("bundle_id")
        raw_digest = tenant_entry.get("bundle_sha256")
        if raw_digest is not None:
            if not isinstance(raw_digest, str) or not raw_digest:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Bundle metadata missing",
                )
            bundle_sha256 = raw_digest
    if not bundle_path_value:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bundle path missing",
        )
    bundle_path = Path(bundle_path_value)
    if not bundle_path.is_absolute():
        bundle_path = REPO_ROOT / bundle_path
    if not bundle_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bundle path missing",
        )
    manifest = _load_yaml_file(bundle_path / "manifest.yaml")
    bundle_id = bundle_id or manifest.get("bundle_id")
    runtime_compatibility = manifest.get("runtime_compatibility", {})
    min_version = runtime_compatibility.get("min_version")
    if not bundle_id or not min_version:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bundle metadata missing",
        )
    return str(bundle_id), str(min_version), bundle_sha256


def _map_error_code(exc: Exception, http_status: int) -> str:
    if http_status == status.HTTP_401_UNAUTHORIZED:
        return "unauthorized"
    if http_status == status.HTTP_403_FORBIDDEN:
        return "forbidden"
    if http_status == status.HTTP_500_INTERNAL_SERVER_ERROR:
        if isinstance(exc.__cause__, (AuthConfigError, AuditConfigError)):
            return "config_error"
        if isinstance(exc, AuthConfigError):
            return "config_error"
        if isinstance(exc, HTTPException) and "config" in str(exc.detail).lower():
            return "config_error"
    return "internal_error"


@app.get("/tenants/{tenant_id}/resolve/current")
def resolve_current(
    tenant_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
) -> dict[str, Any]:
    started_at = time.time()
    request_id = (
        x_request_id
        if isinstance(x_request_id, str) and x_request_id.strip()
        else str(uuid.uuid4())
    )
    status_code = status.HTTP_200_OK
    bundle_id: str | None = None
    error_code: str | None = None

    try:
        enforce_control_plane_auth(
            tenant_id=tenant_id, authorization=authorization, x_tenant_id=x_tenant_id
        )
        bundle_id, min_version, bundle_sha256 = resolve_current_bundle_metadata(tenant_id)
        payload = {
            "bundle_id": bundle_id,
            "runtime_compatibility": {"min_version": min_version},
        }
        if bundle_sha256:
            payload["bundle_sha256"] = bundle_sha256
        return payload
    except HTTPException as exc:
        status_code = exc.status_code
        error_code = _map_error_code(exc, status_code)
        raise
    except AuthConfigError as exc:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = "config_error"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = _map_error_code(exc, status_code)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from exc
    finally:
        event: dict[str, Any] = {
            "ts_utc": now_utc_iso(),
            "service": "control_plane",
            "event": "resolve_current",
            "tenant_id": tenant_id,
            "request_id": request_id,
            "actor": "runtime",
            "outcome": "ok" if status_code < 400 else "error",
            "http_status": int(status_code),
            "latency_ms": int((time.time() - started_at) * 1000),
        }
        if bundle_id:
            event["bundle_id"] = bundle_id
        if error_code:
            event["error_code"] = error_code
        try:
            audit_emit(event)
        except AuditConfigError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc
