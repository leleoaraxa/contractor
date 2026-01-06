# app/runtime/engine/context/control_plane_client.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib import request, error
import json

from app.shared.config.settings import settings
from app.shared.security.auth import outbound_auth_headers


@dataclass(frozen=True)
class ResolveResult:
    bundle_id: Optional[str]
    url: str
    status: str
    detail: Optional[str] = None


class ControlPlaneClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.control_base_url).rstrip("/")
        self.headers = outbound_auth_headers()

    def resolve_bundle_id(self, tenant_id: str, release_alias: str) -> ResolveResult:
        url = f"{self.base_url}/api/v1/control/tenants/{tenant_id}/resolve/{release_alias}"
        req = request.Request(url, method="GET", headers=self.headers)
        try:
            with request.urlopen(req, timeout=5) as resp:
                body = resp.read().decode("utf-8")
                data = json.loads(body) if body else {}
            return ResolveResult(bundle_id=data.get("bundle_id"), url=url, status="ok")
        except error.HTTPError as e:
            try:
                detail = e.read().decode("utf-8")
            except Exception:
                detail = str(e)
            return ResolveResult(bundle_id=None, url=url, status=f"http_{e.code}", detail=detail)
        except Exception as e:
            return ResolveResult(bundle_id=None, url=url, status="error", detail=str(e))
