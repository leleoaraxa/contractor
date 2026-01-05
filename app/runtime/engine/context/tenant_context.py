from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    bundle_id: str
    # In Stage 0 we keep this minimal; later: release_alias, plan, policies, limits, etc.
