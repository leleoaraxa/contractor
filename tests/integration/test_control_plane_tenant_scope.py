# tests/integration/test_control_plane_tenant_scope.py
from __future__ import annotations

import importlib
import sys

from fastapi.testclient import TestClient

TEST_TENANT_ALPHA = "tenant-alpha"
TEST_TENANT_BETA = "tenant-beta"
TEST_API_KEYS = ",".join(
    [
        f"{TEST_TENANT_ALPHA}:tenant_operator:alpha-key",
        f"{TEST_TENANT_BETA}:tenant_operator:beta-key",
    ]
)


def _reload_control_plane_app():
    module_prefix = "app.control_plane."
    for module_name in list(sys.modules):
        if module_name.startswith(module_prefix):
            sys.modules.pop(module_name, None)

    sys.modules.pop("app.shared.config", None)
    sys.modules.pop("app.shared.config.settings", None)

    import app.shared.config.settings as settings_module

    importlib.reload(settings_module)

    main_module = importlib.import_module("app.control_plane.api.main")
    importlib.reload(main_module)
    return main_module.create_app()


def _build_client(monkeypatch, tmp_path) -> TestClient:
    alias_store_path = tmp_path / "tenant_aliases.json"
    monkeypatch.setenv("CONTROL_ALIAS_STORE_PATH", str(alias_store_path))
    monkeypatch.setenv("CONTRACTOR_API_KEYS", TEST_API_KEYS)
    app = _reload_control_plane_app()
    return TestClient(app)


def test_control_plane_accepts_matching_tenant(monkeypatch, tmp_path) -> None:
    client = _build_client(monkeypatch, tmp_path)
    response = client.get(
        f"/api/v1/control/tenants/{TEST_TENANT_ALPHA}/aliases",
        headers={"X-API-Key": "alpha-key"},
    )
    assert response.status_code == 200
    assert response.json()["tenant_id"] == TEST_TENANT_ALPHA


def test_control_plane_rejects_cross_tenant(monkeypatch, tmp_path) -> None:
    client = _build_client(monkeypatch, tmp_path)
    response = client.get(
        f"/api/v1/control/tenants/{TEST_TENANT_BETA}/aliases",
        headers={"X-API-Key": "alpha-key"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "tenant scope mismatch"
