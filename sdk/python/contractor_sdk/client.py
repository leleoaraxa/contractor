from __future__ import annotations

from typing import Any

import requests

from contractor_sdk.config import SDKConfig
from contractor_sdk.errors import ClientError, ServerError


class ContractorClient:
    def __init__(self, config: SDKConfig):
        self._config = config

    @property
    def config(self) -> SDKConfig:
        return self._config

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-API-Key": self._config.api_key,
        }

    def _request(self, method: str, path: str, *, json: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self._config.normalized_base_url()}{path}"
        response = requests.request(
            method=method,
            url=url,
            headers=self._headers(),
            json=json,
            timeout=self._config.timeout,
        )
        if 400 <= response.status_code < 500:
            raise ClientError(
                f"Client error {response.status_code} calling {path}",
                status_code=response.status_code,
                payload=_safe_json(response),
            )
        if 500 <= response.status_code:
            raise ServerError(
                f"Server error {response.status_code} calling {path}",
                status_code=response.status_code,
                payload=_safe_json(response),
            )
        return _safe_json(response)


def _safe_json(response: requests.Response) -> dict[str, Any]:
    if not response.content:
        return {}
    try:
        data = response.json()
    except ValueError:
        return {"raw": response.text}
    if isinstance(data, dict):
        return data
    return {"data": data}
