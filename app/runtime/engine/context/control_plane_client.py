# app/runtime/engine/context/control_plane_client.py
from __future__ import annotations

from typing import Optional
from urllib import request, error
import json

from app.shared.config.settings import settings


class ControlPlaneClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.control_base_url).rstrip("/")

    def resolve_bundle_id(self, tenant_id: str, release_alias: str) -> Optional[str]:
        url = f"{self.base_url}/api/v1/control/tenants/{tenant_id}/resolve/{release_alias}"
        req = request.Request(url, method="GET")
        try:
            with request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("bundle_id")
        except error.HTTPError:
            return None
        except Exception:
            return None
