# tests/test_control_plane_gates.py
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import control_plane

SUITE_TENANT_A_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "bundles"
    / "demo"
    / "faq"
    / "suites"
    / "faq_golden_tenant_a.json"
)

RUNTIME_TENANT_KEYS_JSON = json.dumps(
    {
        "tenant_a": "test-key-a",
        "tenant_b": "test-key-b",
    }
)
RUNTIME_AUDIT_CONFIG_JSON = json.dumps(
    {
        "enabled": True,
        "sink": "stdout",
        "file_path": "data/audit/audit.log.jsonl",
        "retention_days": 7,
    }
)
RUNTIME_RATE_LIMIT_POLICY_JSON = json.dumps(
    {
        "rate_limit": {"window_seconds": 60, "max_requests": 1000},
        "quota": {"window_seconds": 86400, "max_requests": 1000},
        "tenants": {
            "*": {
                "rate_limit": {"window_seconds": 60, "max_requests": 1000},
                "quota": {"window_seconds": 86400, "max_requests": 1000},
            }
        },
    }
)


def _set_cp_env(
    monkeypatch: pytest.MonkeyPatch, auth_path: Path, alias_path: Path
) -> None:
    monkeypatch.setenv(control_plane.AUTH_CONFIG_PATH_ENV, str(auth_path))
    monkeypatch.setenv(control_plane.ALIAS_CONFIG_PATH_ENV, str(alias_path))
    monkeypatch.delenv(control_plane.AUTH_CONFIG_JSON_ENV, raising=False)
    monkeypatch.setenv("CONTRACTOR_TENANT_KEYS", RUNTIME_TENANT_KEYS_JSON)
    monkeypatch.setenv("CONTRACTOR_AUDIT_CONFIG_JSON", RUNTIME_AUDIT_CONFIG_JSON)
    monkeypatch.setenv(
        "CONTRACTOR_RATE_LIMIT_POLICY_JSON", RUNTIME_RATE_LIMIT_POLICY_JSON
    )


@pytest.fixture
def control_plane_auth_config_path(tmp_path: Path) -> Path:
    config = {
        "tenants": {
            "tenant_a": {"token": "cp_test_key_a"},
            "tenant_b": {"token": "cp_test_key_b"},
        }
    }
    path = tmp_path / "tenants.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


@pytest.fixture
def control_plane_alias_config_path(tmp_path: Path) -> Path:
    alias_config = {
        "tenants": {
            "tenant_a": {
                "current_bundle_path": "data/bundles/demo/faq",
                "bundle_id": "demo-faq-0001",
            },
            "tenant_b": {
                "current_bundle_path": "data/bundles/demo/faq",
                "bundle_id": "demo-faq-0001",
            },
        }
    }
    path = tmp_path / "aliases.json"
    path.write_text(json.dumps(alias_config), encoding="utf-8")
    return path


def test_post_gate_executes_bundle_suite_and_returns_completed_result(
    tmp_path: Path,
    control_plane_auth_config_path: Path,
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_total = len(json.loads(SUITE_TENANT_A_PATH.read_text(encoding="utf-8")))

    _set_cp_env(
        monkeypatch, control_plane_auth_config_path, control_plane_alias_config_path
    )
    monkeypatch.setattr(control_plane, "GATE_STORAGE_ROOT", tmp_path / "gates")

    client = TestClient(control_plane.app)
    response = client.post(
        "/tenants/tenant_a/bundles/demo-faq-0001/gates",
        headers={
            "Authorization": "Bearer cp_test_key_a",
            "X-Tenant-Id": "tenant_a",
            "X-Request-Id": "req-gate-1",
        },
        json={"suite_id": "faq_golden_tenant_a"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["gate_id"]
    assert body["request_id"] == "req-gate-1"
    assert body["status"] == "completed"
    assert body["outcome"] == "pass"
    assert body["summary"]["total"] == expected_total
    assert body["summary"]["passed"] == expected_total
    assert body["summary"]["failed"] == 0


def test_get_gate_status_reads_local_storage(
    tmp_path: Path,
    control_plane_auth_config_path: Path,
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_cp_env(
        monkeypatch, control_plane_auth_config_path, control_plane_alias_config_path
    )
    monkeypatch.setattr(control_plane, "GATE_STORAGE_ROOT", tmp_path / "gates")

    client = TestClient(control_plane.app)
    create_response = client.post(
        "/tenants/tenant_a/bundles/demo-faq-0001/gates",
        headers={
            "Authorization": "Bearer cp_test_key_a",
            "X-Tenant-Id": "tenant_a",
            "X-Request-Id": "req-gate-2",
        },
        json={"suite_id": "faq_golden_tenant_a"},
    )
    gate_id = create_response.json()["gate_id"]

    get_response = client.get(
        f"/tenants/tenant_a/bundles/demo-faq-0001/gates/{gate_id}",
        headers={
            "Authorization": "Bearer cp_test_key_a",
            "X-Tenant-Id": "tenant_a",
        },
    )

    assert get_response.status_code == 200
    assert get_response.json()["gate_id"] == gate_id
    assert get_response.json()["request_id"] == "req-gate-2"


def test_gate_history_lists_runs(
    tmp_path: Path,
    control_plane_auth_config_path: Path,
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_cp_env(
        monkeypatch, control_plane_auth_config_path, control_plane_alias_config_path
    )
    monkeypatch.setattr(control_plane, "GATE_STORAGE_ROOT", tmp_path / "gates")

    client = TestClient(control_plane.app)
    for request_id in ("req-gate-3", "req-gate-4"):
        response = client.post(
            "/tenants/tenant_a/bundles/demo-faq-0001/gates",
            headers={
                "Authorization": "Bearer cp_test_key_a",
                "X-Tenant-Id": "tenant_a",
                "X-Request-Id": request_id,
            },
            json={"suite_id": "faq_golden_tenant_a"},
        )
        assert response.status_code == 200

    history_response = client.get(
        "/tenants/tenant_a/bundles/demo-faq-0001/gates/history",
        headers={
            "Authorization": "Bearer cp_test_key_a",
            "X-Tenant-Id": "tenant_a",
        },
    )

    assert history_response.status_code == 200
    body = history_response.json()
    assert body["limit"] == control_plane.GATE_HISTORY_LIMIT
    assert len(body["items"]) == 2
    request_ids = {item["request_id"] for item in body["items"]}
    assert request_ids == {"req-gate-3", "req-gate-4"}


def test_post_gate_rejects_suite_with_cross_tenant_case(
    tmp_path: Path,
    control_plane_auth_config_path: Path,
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_cp_env(
        monkeypatch, control_plane_auth_config_path, control_plane_alias_config_path
    )
    monkeypatch.setattr(control_plane, "GATE_STORAGE_ROOT", tmp_path / "gates")

    bundle_path = tmp_path / "bundle"
    suites_path = bundle_path / "suites"
    suites_path.mkdir(parents=True)
    (bundle_path / "manifest.yaml").write_text(
        "bundle_id: demo-faq-0001\nruntime_compatibility:\n  min_version: '1.0.0'\n",
        encoding="utf-8",
    )
    (suites_path / "faq_golden.json").write_text(
        json.dumps(
            [
                {
                    "tenant_id": "tenant_a",
                    "question": "q1",
                    "expected_answer": "a1",
                },
                {
                    "tenant_id": "tenant_b",
                    "question": "q2",
                    "expected_answer": "a2",
                },
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        control_plane, "_find_bundle_path_by_bundle_id", lambda _bundle_id: bundle_path
    )

    client = TestClient(control_plane.app)
    response = client.post(
        "/tenants/tenant_a/bundles/demo-faq-0001/gates",
        headers={
            "Authorization": "Bearer cp_test_key_a",
            "X-Tenant-Id": "tenant_a",
            "X-Request-Id": "req-gate-cross-tenant",
        },
        json={"suite_id": "faq_golden"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Suite invalid"}
