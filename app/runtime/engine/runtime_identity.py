# app/runtime/engine/runtime_identity.py
from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class RuntimeIdentity:
    dedicated_tenant_id: str | None
    runtime_mode: str
    tenant_scope: str | None


def _normalize_dedicated_tenant_id(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def get_runtime_identity() -> RuntimeIdentity:
    from app.shared.config.settings import settings

    dedicated_tenant_id = _normalize_dedicated_tenant_id(
        getattr(settings, "runtime_dedicated_tenant_id", None)
    )
    if dedicated_tenant_id:
        return RuntimeIdentity(
            dedicated_tenant_id=dedicated_tenant_id,
            runtime_mode="dedicated",
            tenant_scope=dedicated_tenant_id,
        )
    return RuntimeIdentity(
        dedicated_tenant_id=None,
        runtime_mode="shared",
        tenant_scope=None,
    )


def apply_runtime_identity(meta: dict) -> None:
    identity = get_runtime_identity()
    if not meta.get("runtime_mode"):
        meta["runtime_mode"] = identity.runtime_mode
    if identity.tenant_scope is not None:
        if not meta.get("tenant_scope"):
            meta["tenant_scope"] = identity.tenant_scope
