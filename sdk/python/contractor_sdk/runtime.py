from __future__ import annotations

from typing import Any

from contractor_sdk.client import ContractorClient


class RuntimeClient:
    def __init__(self, client: ContractorClient):
        self._client = client

    def ask(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client._request("POST", "/api/v1/runtime/ask", json=payload)
