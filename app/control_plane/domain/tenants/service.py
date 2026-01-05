# app/control_plane/domain/tenants/service.py
from __future__ import annotations

from app.control_plane.domain.tenants.models import TenantAliases
from app.control_plane.domain.tenants.repository import TenantAliasRepository
from app.control_plane.domain.quality.service import QualityService
from app.control_plane.domain.audit.logger import AuditLogger


class TenantAliasService:
    def __init__(
        self,
        repo: TenantAliasRepository,
        quality: QualityService | None = None,
        audit: AuditLogger | None = None,
    ) -> None:
        self.repo = repo
        self.quality = quality or QualityService()
        self.audit = audit or AuditLogger()

    def get_aliases(self, tenant_id: str) -> TenantAliases:
        return self.repo.get(tenant_id)

    def _log_alias_change(
        self, tenant_id: str, alias: str, previous_bundle_id: str | None, new_bundle_id: str
    ) -> None:
        self.audit.log(
            "alias_change",
            {
                "tenant_id": tenant_id,
                "alias": alias,
                "previous_bundle_id": previous_bundle_id,
                "new_bundle_id": new_bundle_id,
            },
        )

    def set_current(self, tenant_id: str, bundle_id: str) -> TenantAliases:
        self.quality.ensure_gate(tenant_id, bundle_id, require_suites=True)
        aliases = self.repo.get(tenant_id)
        previous = aliases.current_bundle_id
        aliases.current_bundle_id = bundle_id
        self.repo.upsert(aliases)
        self._log_alias_change(
            tenant_id=tenant_id,
            alias="current",
            previous_bundle_id=previous,
            new_bundle_id=bundle_id,
        )
        return aliases

    def set_candidate(self, tenant_id: str, bundle_id: str) -> TenantAliases:
        self.quality.ensure_gate(tenant_id, bundle_id, require_suites=True)
        aliases = self.repo.get(tenant_id)
        previous = aliases.candidate_bundle_id
        aliases.candidate_bundle_id = bundle_id
        self.repo.upsert(aliases)
        self._log_alias_change(
            tenant_id=tenant_id,
            alias="candidate",
            previous_bundle_id=previous,
            new_bundle_id=bundle_id,
        )
        return aliases

    def set_draft(self, tenant_id: str, bundle_id: str) -> TenantAliases:
        # Draft must pass validation but not suites (draft is for work)
        self.quality.ensure_gate(tenant_id, bundle_id, require_suites=False)
        aliases = self.repo.get(tenant_id)
        previous = aliases.draft_bundle_id
        aliases.draft_bundle_id = bundle_id
        self.repo.upsert(aliases)
        self._log_alias_change(
            tenant_id=tenant_id,
            alias="draft",
            previous_bundle_id=previous,
            new_bundle_id=bundle_id,
        )
        return aliases

    def resolve(self, tenant_id: str, release_alias: str) -> str | None:
        return self.repo.resolve(tenant_id, release_alias)
