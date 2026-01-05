# app/control_plane/domain/tenants/service.py
from __future__ import annotations

from app.control_plane.domain.tenants.models import TenantAliases
from app.control_plane.domain.tenants.repository import TenantAliasRepository
from app.control_plane.domain.quality.service import QualityService


class TenantAliasService:
    def __init__(self, repo: TenantAliasRepository, quality: QualityService | None = None) -> None:
        self.repo = repo
        self.quality = quality or QualityService()

    def get_aliases(self, tenant_id: str) -> TenantAliases:
        return self.repo.get(tenant_id)

    def set_current(self, tenant_id: str, bundle_id: str) -> TenantAliases:
        self.quality.ensure_gate(tenant_id, bundle_id, require_suites=True)
        aliases = self.repo.get(tenant_id)
        aliases.current_bundle_id = bundle_id
        self.repo.upsert(aliases)
        return aliases

    def set_candidate(self, tenant_id: str, bundle_id: str) -> TenantAliases:
        self.quality.ensure_gate(tenant_id, bundle_id, require_suites=True)
        aliases = self.repo.get(tenant_id)
        aliases.candidate_bundle_id = bundle_id
        self.repo.upsert(aliases)
        return aliases

    def set_draft(self, tenant_id: str, bundle_id: str) -> TenantAliases:
        # Draft must pass validation but not suites (draft is for work)
        self.quality.ensure_gate(tenant_id, bundle_id, require_suites=False)
        aliases = self.repo.get(tenant_id)
        aliases.draft_bundle_id = bundle_id
        self.repo.upsert(aliases)
        return aliases

    def resolve(self, tenant_id: str, release_alias: str) -> str | None:
        return self.repo.resolve(tenant_id, release_alias)
