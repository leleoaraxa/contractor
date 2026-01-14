# tests/integration/test_runtime_identity_contract.py
from __future__ import annotations

import importlib
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


TEST_API_KEY = "test-key-runtime-identity"


def _build_client(
    monkeypatch: pytest.MonkeyPatch, dedicated_tenant_id: str | None
) -> TestClient:
    monkeypatch.setenv("CONTRACTOR_API_KEYS", TEST_API_KEY)
    if dedicated_tenant_id:
        monkeypatch.setenv("RUNTIME_DEDICATED_TENANT_ID", dedicated_tenant_id)
    else:
        monkeypatch.delenv("RUNTIME_DEDICATED_TENANT_ID", raising=False)

    for module_name in (
        "app.runtime.api.main",
        "app.runtime.api.routers.ask",
        "app.runtime.api.routers.healthz",
    ):
        if module_name in sys.modules:
            del sys.modules[module_name]

    import app.shared.config.settings as settings_module

    importlib.reload(settings_module)

    from app.runtime.api.main import app as runtime_app

    return TestClient(runtime_app)


@pytest.fixture()
def dedicated_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    return _build_client(monkeypatch, "tenant-alpha")


@pytest.fixture()
def shared_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    return _build_client(monkeypatch, None)


def _patch_manifest():
    return patch(
        "app.runtime.engine.context.artifact_loader.ArtifactLoader.load_manifest",
        return_value={"_bundle_dir": None, "paths": {}},
    )


def test_dedicated_ask_includes_runtime_identity(dedicated_client: TestClient) -> None:
    ask_payload = {"tenant_id": "tenant-alpha", "question": "ping", "bundle_id": "b1"}
    with _patch_manifest():
        response = dedicated_client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": TEST_API_KEY},
            json=ask_payload,
        )

    assert response.status_code == 200
    meta = response.json()["meta"]
    assert meta["runtime_mode"] == "dedicated"
    assert meta["tenant_scope"] == "tenant-alpha"


def test_dedicated_healthz_includes_runtime_identity(
    dedicated_client: TestClient,
) -> None:
    response = dedicated_client.get("/api/v1/runtime/healthz")

    assert response.status_code == 200
    payload = response.json()
    assert payload["runtime_mode"] == "dedicated"
    assert payload["tenant_scope"] == "tenant-alpha"


def test_shared_runtime_keeps_default_behavior(shared_client: TestClient) -> None:
    ask_payload = {"tenant_id": "tenant-alpha", "question": "ping", "bundle_id": "b1"}
    with _patch_manifest():
        response = shared_client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": TEST_API_KEY},
            json=ask_payload,
        )

    assert response.status_code == 200
    meta = response.json()["meta"]
    assert meta["runtime_mode"] == "shared"
    assert meta.get("tenant_scope") is None

    healthz_response = shared_client.get("/api/v1/runtime/healthz")
    assert healthz_response.status_code == 200
    healthz_payload = healthz_response.json()
    assert healthz_payload["runtime_mode"] == "shared"
    assert healthz_payload["tenant_scope"] is None
