# app/control_plane/domain/bundles/promoter.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from app.shared.config.settings import settings

Alias = Literal["draft", "candidate", "current"]


class AliasConflictError(Exception):
    pass


class AliasNotFoundError(Exception):
    pass


class Promoter:
    """
    Manages bundle aliases (draft, candidate, current) for each tenant.

    In Stage 0, this is a simple file-based store.
    It is NOT thread-safe by design and requires a file lock in a concurrent environment.
    """

    def __init__(self, store_path: str | None = None):
        self.store_path = Path(store_path or settings.control_alias_store_path)
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.store_path.exists():
            self.store_path.write_text("{}")

    def _read_aliases(self) -> dict:
        return json.loads(self.store_path.read_text())

    def _write_aliases(self, aliases: dict) -> None:
        self.store_path.write_text(json.dumps(aliases, indent=2))

    def set_alias(self, tenant_id: str, bundle_id: str, alias: Alias) -> dict:
        """
        Sets an alias for a tenant to a specific bundle_id.
        """
        all_aliases = self._read_aliases()
        tenant_aliases = all_aliases.get(tenant_id, {})
        tenant_aliases[alias] = bundle_id
        all_aliases[tenant_id] = tenant_aliases
        self._write_aliases(all_aliases)
        return tenant_aliases

    def get_alias(self, tenant_id: str, alias: Alias) -> str:
        """
        Resolves an alias to a bundle_id for a tenant.
        """
        all_aliases = self._read_aliases()
        tenant_aliases = all_aliases.get(tenant_id, {})
        bundle_id = tenant_aliases.get(alias)
        if not bundle_id:
            raise AliasNotFoundError(f"Alias '{alias}' not found for tenant '{tenant_id}'")
        return bundle_id

    def get_aliases_for_tenant(self, tenant_id: str) -> dict:
        """
        Returns all aliases for a specific tenant.
        """
        all_aliases = self._read_aliases()
        return all_aliases.get(tenant_id, {})
