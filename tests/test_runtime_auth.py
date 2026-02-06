# tests/test_runtime_auth.py
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.runtime import app


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_golden_case() -> dict[str, str]:
    golden_path = (
        _repo_root()
        / "data"
        / "bundles"
        / "demo"
        / "faq"
        / "suites"
        / "faq_golden.json"
    )
    cases = json.loads(golden_path.read_text(encoding="utf-8"))
    if not cases:
        raise AssertionError("Golden cases are required for runtime auth tests")
    return cases[0]


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_runtime_execute_rejects_missing_headers(client: TestClient) -> None:
    response = client.post("/execute", json={"question": "hello"})

    assert response.status_code == 401


def test_runtime_execute_rejects_unknown_tenant(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "CONTRACTOR_TENANT_KEYS", json.dumps({"tenant_a": "runtime_test_key_a"})
    )

    response = client.post(
        "/execute",
        json={"question": "hello"},
        headers={"X-Tenant-Id": "tenant_unknown", "X-Api-Key": "runtime_test_key_a"},
    )

    assert response.status_code == 403


def test_runtime_execute_rejects_invalid_key(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(
        "CONTRACTOR_TENANT_KEYS", json.dumps({"tenant_a": "runtime_test_key_a"})
    )

    response = client.post(
        "/execute",
        json={"question": "hello"},
        headers={"X-Tenant-Id": "tenant_a", "X-Api-Key": "wrong"},
    )

    assert response.status_code == 403


def test_runtime_execute_fails_closed_when_tenant_key_file_missing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("CONTRACTOR_TENANT_KEYS", raising=False)
    missing_path = tmp_path / "does-not-exist.json"
    monkeypatch.setenv("CONTRACTOR_TENANT_KEYS_PATH", str(missing_path))

    response = client.post(
        "/execute",
        json={"question": "hello"},
        headers={"X-Tenant-Id": "tenant_a", "X-Api-Key": "runtime_test_key_a"},
    )

    assert response.status_code == 500


def test_runtime_execute_fails_closed_when_tenant_keys_env_json_invalid(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CONTRACTOR_TENANT_KEYS", "{invalid")

    response = client.post(
        "/execute",
        json={"question": "hello"},
        headers={"X-Tenant-Id": "tenant_a", "X-Api-Key": "runtime_test_key_a"},
    )

    assert response.status_code == 500


def test_runtime_execute_fails_closed_when_tenant_key_file_json_invalid(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("CONTRACTOR_TENANT_KEYS", raising=False)
    config_path = tmp_path / "tenants.json"
    config_path.write_text("{invalid", encoding="utf-8")
    monkeypatch.setenv("CONTRACTOR_TENANT_KEYS_PATH", str(config_path))

    response = client.post(
        "/execute",
        json={"question": "hello"},
        headers={"X-Tenant-Id": "tenant_a", "X-Api-Key": "runtime_test_key_a"},
    )

    assert response.status_code == 500


def test_runtime_execute_happy_path_with_env_config(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = _load_golden_case()
    tenant_id = case["tenant_id"]
    api_key = "runtime_test_key_happy"
    monkeypatch.setenv("CONTRACTOR_TENANT_KEYS", json.dumps({tenant_id: api_key}))

    response = client.post(
        "/execute",
        json={"question": case["question"]},
        headers={"X-Tenant-Id": tenant_id, "X-Api-Key": api_key},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == tenant_id
    assert payload["status"] == "ok"
    assert case["expected_answer"] in payload["output_text"]
