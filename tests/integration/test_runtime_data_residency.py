# tests/integration/test_runtime_data_residency.py
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
        "tenant-alpha:tenant_runtime_client:alpha-key",
        "tenant-beta:tenant_runtime_client:beta-key",
    ]
)


def _build_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    dedicated_tenant_id: str | None,
    runtime_region: str | None,
    residency_requirements: str | None,
) -> TestClient:
    monkeypatch.setenv("CONTRACTOR_API_KEYS", TEST_API_KEYS)
    if dedicated_tenant_id:
        monkeypatch.setenv("RUNTIME_DEDICATED_TENANT_ID", dedicated_tenant_id)
    else:
        monkeypatch.delenv("RUNTIME_DEDICATED_TENANT_ID", raising=False)

    if runtime_region:
        monkeypatch.setenv("RUNTIME_REGION", runtime_region)
    else:
        monkeypatch.delenv("RUNTIME_REGION", raising=False)

    if residency_requirements:
        monkeypatch.setenv("RUNTIME_TENANT_RESIDENCY_REQUIREMENTS", residency_requirements)
    else:
        monkeypatch.delenv("RUNTIME_TENANT_RESIDENCY_REQUIREMENTS", raising=False)

    for module_name in (
        "app.runtime.api.main",
        "app.runtime.api.routers.ask",
        "app.runtime.api.routers.healthz",
        "app.runtime.engine.ask_handler",
        "app.runtime.engine.data_residency",
        "app.runtime.engine.runtime_identity",
        "app.shared.config.settings",
    ):
        if module_name in sys.modules:
            del sys.modules[module_name]

    import app.shared.config.settings as settings_module

    importlib.reload(settings_module)

    from app.runtime.api.main import app as runtime_app

    return TestClient(runtime_app)


def _patch_manifest():
    return patch(
        "app.runtime.engine.context.artifact_loader.ArtifactLoader.load_manifest",
        return_value={"_bundle_dir": None, "paths": {}},
    )


@pytest.fixture()
def dedicated_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    return _build_client(
        monkeypatch,
        dedicated_tenant_id="tenant-alpha",
        runtime_region="sa-east-1",
        residency_requirements=None,
    )


def test_healthz_includes_data_residency(dedicated_client: TestClient) -> None:
    response = dedicated_client.get("/api/v1/runtime/healthz")

    assert response.status_code == 200
    payload = response.json()
    data_residency = payload["data_residency"]
    assert data_residency["runtime_region"] == "sa-east-1"
    assert "residency_applies_to" in data_residency
    assert "residency_not_applicable_to" in data_residency
    assert "explicit_non_guarantees" in data_residency


def test_ask_meta_includes_data_residency(dedicated_client: TestClient) -> None:
    ask_payload = {"tenant_id": "tenant-alpha", "question": "ping", "bundle_id": "b1"}
    with _patch_manifest():
        response = dedicated_client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": "alpha-key"},
            json=ask_payload,
        )

    assert response.status_code == 200
    meta = response.json()["meta"]
    data_residency = meta["data_residency"]
    assert data_residency["runtime_region"] == "sa-east-1"
    assert data_residency["data_classes"]["A"] == "platform_metadata"


def test_dedicated_residency_allows_match(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        monkeypatch,
        dedicated_tenant_id="tenant-alpha",
        runtime_region="sa-east-1",
        residency_requirements="tenant-alpha=sa-east-1",
    )
    ask_payload = {"tenant_id": "tenant-alpha", "question": "ping", "bundle_id": "b1"}
    with _patch_manifest():
        response = client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": "alpha-key"},
            json=ask_payload,
        )

    assert response.status_code == 200


def test_dedicated_residency_rejects_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        monkeypatch,
        dedicated_tenant_id="tenant-alpha",
        runtime_region="us-east-1",
        residency_requirements="tenant-alpha=sa-east-1",
    )
    ask_payload = {"tenant_id": "tenant-alpha", "question": "ping", "bundle_id": "b1"}
    with _patch_manifest():
        response = client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": "alpha-key"},
            json=ask_payload,
        )

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["error"] == "residency_region_mismatch"
    assert detail["type"] == "auth"
    assert detail["details"]["runtime_region"] == "us-east-1"
    assert detail["details"]["required_region"] == "sa-east-1"


def test_dedicated_residency_rejects_missing_runtime_region(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _build_client(
        monkeypatch,
        dedicated_tenant_id="tenant-alpha",
        runtime_region=None,
        residency_requirements="tenant-alpha=sa-east-1",
    )
    ask_payload = {"tenant_id": "tenant-alpha", "question": "ping", "bundle_id": "b1"}
    with _patch_manifest():
        response = client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": "alpha-key"},
            json=ask_payload,
        )

    assert response.status_code == 403
    detail = response.json()["detail"]
    assert detail["error"] == "residency_region_not_configured"
    assert detail["type"] == "auth"


def test_shared_runtime_does_not_enforce_residency(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(
        monkeypatch,
        dedicated_tenant_id=None,
        runtime_region=None,
        residency_requirements="tenant-alpha=sa-east-1",
    )
    ask_payload = {"tenant_id": "tenant-alpha", "question": "ping", "bundle_id": "b1"}
    with _patch_manifest():
        response = client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": "alpha-key"},
            json=ask_payload,
        )

    assert response.status_code == 200
