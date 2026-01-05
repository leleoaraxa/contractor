# app/control_plane/domain/tenants/models.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TenantAliases:
    tenant_id: str
    current_bundle_id: Optional[str] = None
    candidate_bundle_id: Optional[str] = None
    draft_bundle_id: Optional[str] = None
