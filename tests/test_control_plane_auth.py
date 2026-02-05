from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import control_plane


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


def _set_cp_env(monkeypatch: pytest.MonkeyPatch, auth_path: Path, alias_path: Path) -> None:
    monkeypatch.setenv(control_plane.AUTH_CONFIG_PATH_ENV, str(auth_path))
    monkeypatch.setenv(control_plane.ALIAS_CONFIG_PATH_ENV, str(alias_path))
    monkeypatch.delenv(control_plane.AUTH_CONFIG_JSON_ENV, raising=False)


def test_control_plane_rejects_missing_authorization_header(
    control_plane_auth_config_path: Path,
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_cp_env(monkeypatch, control_plane_auth_config_path, control_plane_alias_config_path)
    client = TestClient(control_plane.app)

    response = client.get(
        "/tenants/tenant_a/resolve/current",
        headers={"X-Tenant-Id": "tenant_a"},
    )

    assert response.status_code == 401


def test_control_plane_rejects_invalid_token(
    control_plane_auth_config_path: Path,
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_cp_env(monkeypatch, control_plane_auth_config_path, control_plane_alias_config_path)
    client = TestClient(control_plane.app)

    response = client.get(
        "/tenants/tenant_a/resolve/current",
        headers={
            "Authorization": "Bearer invalid_token",
            "X-Tenant-Id": "tenant_a",
        },
    )

    assert response.status_code == 401


def test_control_plane_rejects_tenant_mismatch_between_token_header_and_path(
    control_plane_auth_config_path: Path,
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_cp_env(monkeypatch, control_plane_auth_config_path, control_plane_alias_config_path)
    client = TestClient(control_plane.app)

    response = client.get(
        "/tenants/tenant_b/resolve/current",
        headers={
            "Authorization": "Bearer cp_test_key_a",
            "X-Tenant-Id": "tenant_a",
        },
    )

    assert response.status_code == 403


def test_control_plane_returns_current_bundle_for_valid_request(
    control_plane_auth_config_path: Path,
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _set_cp_env(monkeypatch, control_plane_auth_config_path, control_plane_alias_config_path)
    client = TestClient(control_plane.app)

    response = client.get(
        "/tenants/tenant_a/resolve/current",
        headers={
            "Authorization": "Bearer cp_test_key_a",
            "X-Tenant-Id": "tenant_a",
        },
    )

    assert response.status_code == 200
    assert response.json()["bundle_id"] == "demo-faq-0001"
    assert response.json()["runtime_compatibility"]["min_version"]


def test_control_plane_fails_closed_with_missing_auth_config(
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(control_plane.AUTH_CONFIG_PATH_ENV, "non-existent-tenants.json")
    monkeypatch.setenv(control_plane.ALIAS_CONFIG_PATH_ENV, str(control_plane_alias_config_path))
    monkeypatch.delenv(control_plane.AUTH_CONFIG_JSON_ENV, raising=False)

    client = TestClient(control_plane.app)
    response = client.get(
        "/tenants/tenant_a/resolve/current",
        headers={
            "Authorization": "Bearer cp_test_key_a",
            "X-Tenant-Id": "tenant_a",
        },
    )

    assert response.status_code == 500


def test_control_plane_fails_closed_with_invalid_auth_config_json(
    control_plane_alias_config_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(control_plane.AUTH_CONFIG_JSON_ENV, "{invalid-json")
    monkeypatch.setenv(control_plane.ALIAS_CONFIG_PATH_ENV, str(control_plane_alias_config_path))

    client = TestClient(control_plane.app)
    response = client.get(
        "/tenants/tenant_a/resolve/current",
        headers={
            "Authorization": "Bearer cp_test_key_a",
            "X-Tenant-Id": "tenant_a",
        },
    )

    assert response.status_code == 500


def test_load_tenant_token_index_rejects_duplicate_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        control_plane.AUTH_CONFIG_JSON_ENV,
        json.dumps(
            {
                "tenants": {
                    "tenant_a": {"token": "shared"},
                    "tenant_b": {"token": "shared"},
                }
            }
        ),
    )

    with pytest.raises(control_plane.AuthConfigError):
        control_plane.load_tenant_token_index()
