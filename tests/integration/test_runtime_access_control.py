# tests/integration/test_runtime_access_control.py
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TEST_API_KEYS = ",".join(
    [
        "legacy-key",
        "tenant-alpha:tenant_runtime_client:alpha-key",
        "tenant-alpha:tenant_operator:operator-key",
        "tenant-beta:tenant_runtime_client:beta-key",
    ]
)


def _build_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("CONTRACTOR_API_KEYS", TEST_API_KEYS)
    monkeypatch.delenv("RUNTIME_DEDICATED_TENANT_ID", raising=False)

    for module_name in (
        "app.runtime.api.main",
        "app.runtime.api.routers.ask",
        "app.runtime.engine.ask_handler",
        "app.runtime.engine.runtime_identity",
        "app.shared.config.settings",
    ):
        if module_name in sys.modules:
            del sys.modules[module_name]

    import app.shared.config.settings as settings_module

    importlib.reload(settings_module)

    from app.runtime.api.main import app as runtime_app

    return TestClient(runtime_app)


@pytest.fixture()
def runtime_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    return _build_client(monkeypatch)


def _patch_manifest():
    return patch(
        "app.runtime.engine.context.artifact_loader.ArtifactLoader.load_manifest",
        return_value={"_bundle_dir": None, "paths": {}},
    )


def test_runtime_accepts_tenant_scoped_key(runtime_client: TestClient) -> None:
    ask_payload = {"tenant_id": "tenant-alpha", "question": "ping", "bundle_id": "b1"}
    with _patch_manifest():
        response = runtime_client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": "alpha-key"},
            json=ask_payload,
        )

    assert response.status_code == 200


def test_runtime_rejects_mismatched_tenant_key(runtime_client: TestClient) -> None:
    ask_payload = {"tenant_id": "tenant-alpha", "question": "ping", "bundle_id": "b1"}
    with _patch_manifest():
        response = runtime_client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": "beta-key"},
            json=ask_payload,
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "tenant scope mismatch"


def test_runtime_rejects_wrong_role(runtime_client: TestClient) -> None:
    ask_payload = {"tenant_id": "tenant-alpha", "question": "ping", "bundle_id": "b1"}
    with _patch_manifest():
        response = runtime_client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": "operator-key"},
            json=ask_payload,
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "identity role not allowed"


def test_runtime_rejects_unscoped_key(runtime_client: TestClient) -> None:
    ask_payload = {"tenant_id": "tenant-alpha", "question": "ping", "bundle_id": "b1"}
    with _patch_manifest():
        response = runtime_client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": "legacy-key"},
            json=ask_payload,
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "tenant scope required"
