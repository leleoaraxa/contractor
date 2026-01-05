from __future__ import annotations

import re

TENANT_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def validate_tenant_id(tenant_id: str) -> None:
    if not tenant_id or not TENANT_ID_RE.match(tenant_id):
        raise ValueError("invalid tenant_id: must match ^[A-Za-z0-9._-]+$ (no slashes)")
