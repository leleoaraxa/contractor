# tests/integration/test_error_contracts.py
from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TEST_API_KEY = "test-key"
TEST_TENANT_ID = "demo"


def _build_control_plane_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv(
        "CONTRACTOR_API_KEYS",
        f"{TEST_TENANT_ID}:tenant_runtime_client:{TEST_API_KEY}",
    )

    for module_name in (
        "app.control_plane.api.main",
        "app.control_plane.api.routers.quality",
        "app.shared.config.settings",
    ):
        if module_name in sys.modules:
            del sys.modules[module_name]

    import app.shared.config.settings as settings_module

    importlib.reload(settings_module)

    from app.control_plane.api.main import app as control_plane_app

    return TestClient(control_plane_app)


def test_control_plane_not_found_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_control_plane_client(monkeypatch)

    from app.control_plane.api.routers import quality as quality_router

    def _missing_report(*_args, **_kwargs):
        raise FileNotFoundError("missing")

    monkeypatch.setattr(quality_router._svc, "get_report", _missing_report)

    response = client.get(
        f"/api/v1/control/tenants/{TEST_TENANT_ID}/bundles/missing/quality",
        headers={"X-API-Key": TEST_API_KEY},
    )

    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["error"] == "quality_report_not_found"
    assert detail["type"] == "not_found"
