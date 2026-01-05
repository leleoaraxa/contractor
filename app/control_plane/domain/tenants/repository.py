# app/control_plane/domain/tenants/repository.py
from __future__ import annotations

from typing import Dict, Optional

from app.control_plane.domain.tenants.models import TenantAliases


class TenantAliasRepository:
    """
    Stage 0: in-memory registry.
    Stage 1+: RDS/Postgres-backed (ADR 0004).
    """

    def __init__(self) -> None:
        self._tenants: Dict[str, TenantAliases] = {}

    def get(self, tenant_id: str) -> TenantAliases:
        return self._tenants.get(tenant_id) or TenantAliases(tenant_id=tenant_id)

    def upsert(self, aliases: TenantAliases) -> None:
        self._tenants[aliases.tenant_id] = aliases

    def resolve(self, tenant_id: str, release_alias: str) -> Optional[str]:
        aliases = self.get(tenant_id)
        if release_alias == "current":
            return aliases.current_bundle_id
        if release_alias == "candidate":
            return aliases.candidate_bundle_id
        if release_alias == "draft":
            return aliases.draft_bundle_id
        return None
