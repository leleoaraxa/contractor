from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import control_plane
from tests.test_control_plane_gates import _set_cp_env


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
            }
        }
    }
    path = tmp_path / "aliases.json"
    path.write_text(json.dumps(alias_config), encoding="utf-8")
    return path


def _mk_bundle(tmp_path: Path, bundle_id: str) -> Path:
    bundle_path = tmp_path / "bundles" / bundle_id
    bundle_path.mkdir(parents=True, exist_ok=True)
    (bundle_path / "manifest.yaml").write_text(
        f"bundle_id: {bundle_id}\nruntime_compatibility:\n  min_version: '1.0.0'\n",
        encoding="utf-8",
    )
    return bundle_path


def _write_gate_pass(root: Path, tenant_id: str, bundle_id: str, gate_id: str = "gate-1") -> None:
    path = root / tenant_id / bundle_id / f"{gate_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "gate_id": gate_id,
        "request_id": "req-gate",
        "tenant_id": tenant_id,
        "bundle_id": bundle_id,
        "status": "completed",
        "outcome": "pass",
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _headers(token: str, tenant_id: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": tenant_id,
        "X-Request-Id": "req-1",
    }


def test_set_candidate_persists_and_is_idempotent(
    tmp_path: Path,
    control_plane_auth_config_path: Path,
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_cp_env(monkeypatch, control_plane_auth_config_path, control_plane_alias_config_path)
    monkeypatch.setattr(control_plane, "ALIAS_STATE_ROOT", tmp_path / "alias_state")

    bundle_path = _mk_bundle(tmp_path, "demo-faq-0001")
    monkeypatch.setattr(
        control_plane, "_find_bundle_path_by_bundle_id", lambda _bundle_id: bundle_path
    )

    client = TestClient(control_plane.app)
    response = client.post(
        "/tenants/tenant_a/aliases/candidate",
        headers=_headers("cp_test_key_a", "tenant_a"),
        json={"bundle_id": "demo-faq-0001"},
    )
    assert response.status_code == 200
    assert response.json()["aliases"]["candidate"] == {"bundle_id": "demo-faq-0001"}

    response2 = client.post(
        "/tenants/tenant_a/aliases/candidate",
        headers=_headers("cp_test_key_a", "tenant_a"),
        json={"bundle_id": "demo-faq-0001"},
    )
    assert response2.status_code == 200
    state = json.loads((tmp_path / "alias_state" / "tenant_a.json").read_text(encoding="utf-8"))
    assert state["aliases"]["candidate"] == {"bundle_id": "demo-faq-0001"}


def test_promote_requires_candidate(
    tmp_path: Path,
    control_plane_auth_config_path: Path,
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_cp_env(monkeypatch, control_plane_auth_config_path, control_plane_alias_config_path)
    monkeypatch.setattr(control_plane, "ALIAS_STATE_ROOT", tmp_path / "alias_state")
    monkeypatch.setattr(control_plane, "GATE_STORAGE_ROOT", tmp_path / "gates")

    client = TestClient(control_plane.app)
    response = client.post(
        "/tenants/tenant_a/aliases/promote",
        headers=_headers("cp_test_key_a", "tenant_a"),
    )
    assert response.status_code == 409


def test_promote_requires_gate_pass(
    tmp_path: Path,
    control_plane_auth_config_path: Path,
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_cp_env(monkeypatch, control_plane_auth_config_path, control_plane_alias_config_path)
    monkeypatch.setattr(control_plane, "ALIAS_STATE_ROOT", tmp_path / "alias_state")
    monkeypatch.setattr(control_plane, "GATE_STORAGE_ROOT", tmp_path / "gates")

    bundle_path = _mk_bundle(tmp_path, "demo-faq-0001")
    monkeypatch.setattr(
        control_plane, "_find_bundle_path_by_bundle_id", lambda _bundle_id: bundle_path
    )

    client = TestClient(control_plane.app)
    set_response = client.post(
        "/tenants/tenant_a/aliases/candidate",
        headers=_headers("cp_test_key_a", "tenant_a"),
        json={"bundle_id": "demo-faq-0001"},
    )
    assert set_response.status_code == 200

    response = client.post(
        "/tenants/tenant_a/aliases/promote",
        headers=_headers("cp_test_key_a", "tenant_a"),
    )
    assert response.status_code == 409


def test_promote_happy_path_and_idempotent(
    tmp_path: Path,
    control_plane_auth_config_path: Path,
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_cp_env(monkeypatch, control_plane_auth_config_path, control_plane_alias_config_path)
    monkeypatch.setattr(control_plane, "ALIAS_STATE_ROOT", tmp_path / "alias_state")
    monkeypatch.setattr(control_plane, "GATE_STORAGE_ROOT", tmp_path / "gates")

    bundle_path = _mk_bundle(tmp_path, "demo-faq-0001")
    monkeypatch.setattr(
        control_plane, "_find_bundle_path_by_bundle_id", lambda _bundle_id: bundle_path
    )
    _write_gate_pass(tmp_path / "gates", "tenant_a", "demo-faq-0001")

    client = TestClient(control_plane.app)
    client.post(
        "/tenants/tenant_a/aliases/candidate",
        headers=_headers("cp_test_key_a", "tenant_a"),
        json={"bundle_id": "demo-faq-0001"},
    )

    response = client.post(
        "/tenants/tenant_a/aliases/promote",
        headers=_headers("cp_test_key_a", "tenant_a"),
    )
    assert response.status_code == 200
    assert response.json()["aliases"]["current"] == {"bundle_id": "demo-faq-0001"}

    response2 = client.post(
        "/tenants/tenant_a/aliases/promote",
        headers=_headers("cp_test_key_a", "tenant_a"),
    )
    assert response2.status_code == 200
    assert response2.json()["aliases"]["current"] == {"bundle_id": "demo-faq-0001"}


def test_rollback_requires_gate_pass(
    tmp_path: Path,
    control_plane_auth_config_path: Path,
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_cp_env(monkeypatch, control_plane_auth_config_path, control_plane_alias_config_path)
    monkeypatch.setattr(control_plane, "ALIAS_STATE_ROOT", tmp_path / "alias_state")
    monkeypatch.setattr(control_plane, "GATE_STORAGE_ROOT", tmp_path / "gates")

    client = TestClient(control_plane.app)
    response = client.post(
        "/tenants/tenant_a/aliases/rollback",
        headers=_headers("cp_test_key_a", "tenant_a"),
        json={"bundle_id": "demo-faq-0002"},
    )
    assert response.status_code == 409


def test_rollback_happy_path(
    tmp_path: Path,
    control_plane_auth_config_path: Path,
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_cp_env(monkeypatch, control_plane_auth_config_path, control_plane_alias_config_path)
    monkeypatch.setattr(control_plane, "ALIAS_STATE_ROOT", tmp_path / "alias_state")
    monkeypatch.setattr(control_plane, "GATE_STORAGE_ROOT", tmp_path / "gates")
    _write_gate_pass(tmp_path / "gates", "tenant_a", "demo-faq-0002")

    client = TestClient(control_plane.app)
    response = client.post(
        "/tenants/tenant_a/aliases/rollback",
        headers=_headers("cp_test_key_a", "tenant_a"),
        json={"bundle_id": "demo-faq-0002"},
    )
    assert response.status_code == 200
    assert response.json()["aliases"]["current"] == {"bundle_id": "demo-faq-0002"}


def test_alias_endpoints_enforce_tenant_isolation(
    tmp_path: Path,
    control_plane_auth_config_path: Path,
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_cp_env(monkeypatch, control_plane_auth_config_path, control_plane_alias_config_path)
    monkeypatch.setattr(control_plane, "ALIAS_STATE_ROOT", tmp_path / "alias_state")

    client = TestClient(control_plane.app)
    response = client.post(
        "/tenants/tenant_a/aliases/promote",
        headers={
            "Authorization": "Bearer cp_test_key_a",
            "X-Tenant-Id": "tenant_b",
        },
    )
    assert response.status_code == 403
