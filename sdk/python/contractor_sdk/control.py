from __future__ import annotations

from typing import Any

from contractor_sdk.client import ContractorClient


class ControlClient:
    def __init__(self, client: ContractorClient):
        self._client = client

    def healthz(self) -> dict[str, Any]:
        return self._client._request("GET", "/api/v1/control/healthz")

    def set_current_alias(self, tenant_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        path = f"/api/v1/control/tenants/{tenant_id}/aliases/current"
        return self._client._request("POST", path, json=payload)

    def resolve_current_version(self, tenant_id: str) -> dict[str, Any]:
        path = f"/api/v1/control/tenants/{tenant_id}/versions/current/resolve"
        return self._client._request("GET", path)

    def resolve_current_alias(self, tenant_id: str) -> dict[str, Any]:
        path = f"/api/v1/control/tenants/{tenant_id}/resolve/current"
        return self._client._request("GET", path)
