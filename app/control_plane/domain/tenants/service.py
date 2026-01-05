# app/control_plane/domain/tenants/service.py
from __future__ import annotations

from app.control_plane.domain.tenants.models import TenantAliases
from app.control_plane.domain.tenants.repository import TenantAliasRepository


class TenantAliasService:
    def __init__(self, repo: TenantAliasRepository) -> None:
        self.repo = repo

    def get_aliases(self, tenant_id: str) -> TenantAliases:
        return self.repo.get(tenant_id)

    def set_current(self, tenant_id: str, bundle_id: str) -> TenantAliases:
        aliases = self.repo.get(tenant_id)
        aliases.current_bundle_id = bundle_id
        self.repo.upsert(aliases)
        return aliases

    def set_candidate(self, tenant_id: str, bundle_id: str) -> TenantAliases:
        aliases = self.repo.get(tenant_id)
        aliases.candidate_bundle_id = bundle_id
        self.repo.upsert(aliases)
        return aliases

    def set_draft(self, tenant_id: str, bundle_id: str) -> TenantAliases:
        aliases = self.repo.get(tenant_id)
        aliases.draft_bundle_id = bundle_id
        self.repo.upsert(aliases)
        return aliases

    def resolve(self, tenant_id: str, release_alias: str) -> str | None:
        return self.repo.resolve(tenant_id, release_alias)
