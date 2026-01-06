from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from app.control_plane.domain.tenants.models import TenantAliases
from app.shared.config.settings import settings


class TenantAliasRepository:
    """
    Stage 0: file-backed JSON store to survive reloads.
    Stage 1+: DB-backed (ADR 0004).
    """

    def __init__(self, store_path: str | None = None) -> None:
        self.store_path = Path(store_path or settings.control_alias_store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_all(self) -> Dict[str, TenantAliases]:
        if not self.store_path.exists():
            return {}
        raw = json.loads(self.store_path.read_text(encoding="utf-8") or "{}")
        out: Dict[str, TenantAliases] = {}
        for tenant_id, v in (raw or {}).items():
            out[tenant_id] = TenantAliases(
                tenant_id=tenant_id,
                current_bundle_id=v.get("current"),
                candidate_bundle_id=v.get("candidate"),
                draft_bundle_id=v.get("draft"),
            )
        return out

    def _write_all(self, data: Dict[str, TenantAliases]) -> None:
        raw = {
            tid: {
                "draft": a.draft_bundle_id,
                "candidate": a.candidate_bundle_id,
                "current": a.current_bundle_id,
            }
            for tid, a in data.items()
        }
        self.store_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, tenant_id: str) -> TenantAliases:
        all_ = self._read_all()
        return all_.get(tenant_id) or TenantAliases(tenant_id=tenant_id)

    def upsert(self, aliases: TenantAliases) -> None:
        all_ = self._read_all()
        all_[aliases.tenant_id] = aliases
        self._write_all(all_)

    def resolve(self, tenant_id: str, release_alias: str) -> Optional[str]:
        aliases = self.get(tenant_id)
        if release_alias == "current":
            return aliases.current_bundle_id
        if release_alias == "candidate":
            return aliases.candidate_bundle_id
        if release_alias == "draft":
            return aliases.draft_bundle_id
        return None
