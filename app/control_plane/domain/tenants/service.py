# app/control_plane/domain/tenants/service.py
from __future__ import annotations

import hashlib

from app.control_plane.domain.tenants.models import TenantAliases
from app.control_plane.domain.tenants.repository import TenantAliasRepository
from app.control_plane.domain.quality.service import PromotionGateError, QualityService
from app.control_plane.domain.audit.logger import AuditLogger
from app.shared.security.auth import ApiKeyIdentity


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

    @staticmethod
    def _format_actor(identity: ApiKeyIdentity | None) -> str:
        if identity is None or not identity.key:
            return "unknown"
        digest = hashlib.sha256(identity.key.encode("utf-8")).hexdigest()[:12]
        return f"key_hash:{digest}"

    def _log_alias_change(
        self,
        tenant_id: str,
        alias: str,
        previous_bundle_id: str | None,
        new_bundle_id: str,
        *,
        actor: ApiKeyIdentity | None,
    ) -> None:
        self.audit.log(
            "alias.set",
            {
                "tenant_id": tenant_id,
                "actor": self._format_actor(actor),
                "target": {"alias": alias, "bundle_id": new_bundle_id},
                "previous_bundle_id": previous_bundle_id,
            },
        )

    def set_current(
        self, tenant_id: str, bundle_id: str, actor: ApiKeyIdentity | None = None
    ) -> TenantAliases:
        self.quality.ensure_gate(
            tenant_id, bundle_id, require_suites=True, require_template_safety=True
        )
        aliases = self.repo.get(tenant_id)
        previous = aliases.current_bundle_id
        aliases.current_bundle_id = bundle_id
        self.repo.upsert(aliases)
        self._log_alias_change(
            tenant_id=tenant_id,
            alias="current",
            previous_bundle_id=previous,
            new_bundle_id=bundle_id,
            actor=actor,
        )
        return aliases

    def set_candidate(
        self, tenant_id: str, bundle_id: str, actor: ApiKeyIdentity | None = None
    ) -> TenantAliases:
        self.quality.ensure_gate(
            tenant_id, bundle_id, require_suites=True, require_template_safety=True
        )
        aliases = self.repo.get(tenant_id)
        previous = aliases.candidate_bundle_id
        aliases.candidate_bundle_id = bundle_id
        self.repo.upsert(aliases)
        self._log_alias_change(
            tenant_id=tenant_id,
            alias="candidate",
            previous_bundle_id=previous,
            new_bundle_id=bundle_id,
            actor=actor,
        )
        return aliases

    def set_draft(
        self, tenant_id: str, bundle_id: str, actor: ApiKeyIdentity | None = None
    ) -> TenantAliases:
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
            actor=actor,
        )
        return aliases

    def resolve(self, tenant_id: str, release_alias: str) -> str | None:
        return self.repo.resolve(tenant_id, release_alias)

    @staticmethod
    def format_gate_error(exc: PromotionGateError) -> dict:
        return {
            "error": "promotion_gate_failed",
            "gate": exc.gate,
            "detail": exc.detail,
            "report_path": exc.report_path,
        }
