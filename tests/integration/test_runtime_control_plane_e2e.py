# tests/integration/test_runtime_control_plane_e2e.py
import json
import shutil
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app import runtime
from app.runtime import app


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_tenant_keys() -> dict[str, str]:
    tenant_path = _repo_root() / "data" / "runtime" / "tenants.json"
    return json.loads(tenant_path.read_text(encoding="utf-8"))


def _load_bundle_metadata() -> tuple[Path, str, str]:
    bundle_path = _repo_root() / "data" / "bundles" / "demo" / "faq"
    manifest = yaml.safe_load(
        (bundle_path / "manifest.yaml").read_text(encoding="utf-8")
    )
    bundle_id = manifest.get("bundle_id")
    min_version = manifest.get("runtime_compatibility", {}).get("min_version")
    return bundle_path, bundle_id, min_version


def _prepare_bundle_cache_hit(
    tmp_path: Path, bundle_id: str, source_bundle_path: Path
) -> Path:
    bundle_root = tmp_path / "bundles"
    target = bundle_root / bundle_id
    if target.exists():
        return bundle_root
    shutil.copytree(source_bundle_path, target)
    return bundle_root


def _select_tenant_id(tenant_keys: dict[str, str]) -> str:
    if not tenant_keys:
        raise AssertionError("No tenants found")
    return sorted(tenant_keys.keys())[0]


@contextmanager
def control_plane_server(
    tenant_id: str, status_code: int, response_body: bytes
) -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            expected_path = f"/tenants/{tenant_id}/resolve/current"
            if self.path != expected_path:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response_body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


@pytest.fixture
def alias_config_path(tmp_path: Path) -> Path:
    bundle_path, bundle_id, _ = _load_bundle_metadata()
    alias_config = {
        "tenants": {
            "*": {
                "current_bundle_path": str(bundle_path),
                "bundle_id": bundle_id,
            }
        }
    }
    config_path = tmp_path / "aliases.json"
    config_path.write_text(json.dumps(alias_config), encoding="utf-8")
    return config_path


def test_runtime_control_plane_e2e_executes_with_current_alias(
    alias_config_path: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    tenant_keys = _load_tenant_keys()
    tenant_id = _select_tenant_id(tenant_keys)
    bundle_path, bundle_id, min_version = _load_bundle_metadata()
    response_body = json.dumps(
        {"bundle_id": bundle_id, "runtime_compatibility": {"min_version": min_version}}
    ).encode("utf-8")
    bundle_root = _prepare_bundle_cache_hit(tmp_path, bundle_id, bundle_path)
    monkeypatch.setattr(runtime, "_bundle_root", lambda: bundle_root)

    with control_plane_server(tenant_id, 200, response_body) as base_url:
        monkeypatch.setenv("CONTRACTOR_CONTROL_PLANE_BASE_URL", base_url)
        monkeypatch.setenv("CONTRACTOR_ALIAS_CONFIG_PATH", str(alias_config_path))

        client = TestClient(app)
        headers = {"X-Tenant-Id": tenant_id, "X-Api-Key": tenant_keys[tenant_id]}
        request_payload = {"question": "O que é o CONTRACTOR?"}

        response = client.post("/execute", json=request_payload, headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["bundle_id"] == bundle_id
    assert payload["intent"] == "faq_query"
    assert payload["status"] in {"ok", "no_match"}
    assert isinstance(payload["output_text"], str)
    assert (bundle_path / "manifest.yaml").exists()


def test_runtime_control_plane_fail_closed_on_http_error(
    alias_config_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tenant_keys = _load_tenant_keys()
    tenant_id = _select_tenant_id(tenant_keys)

    with control_plane_server(tenant_id, 500, b"") as base_url:
        monkeypatch.setenv("CONTRACTOR_CONTROL_PLANE_BASE_URL", base_url)
        monkeypatch.setenv("CONTRACTOR_ALIAS_CONFIG_PATH", str(alias_config_path))

        client = TestClient(app)
        headers = {"X-Tenant-Id": tenant_id, "X-Api-Key": tenant_keys[tenant_id]}

        response = client.post(
            "/execute", json={"question": "irrelevant"}, headers=headers
        )

    assert response.status_code == 503
    assert response.json()["detail"] == "Control Plane error: 500"


def test_runtime_control_plane_fail_closed_on_invalid_payload(
    alias_config_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tenant_keys = _load_tenant_keys()
    tenant_id = _select_tenant_id(tenant_keys)
    _, bundle_id, _ = _load_bundle_metadata()
    response_body = json.dumps({"bundle_id": bundle_id}).encode("utf-8")

    with control_plane_server(tenant_id, 200, response_body) as base_url:
        monkeypatch.setenv("CONTRACTOR_CONTROL_PLANE_BASE_URL", base_url)
        monkeypatch.setenv("CONTRACTOR_ALIAS_CONFIG_PATH", str(alias_config_path))

        client = TestClient(app)
        headers = {"X-Tenant-Id": tenant_id, "X-Api-Key": tenant_keys[tenant_id]}

        response = client.post(
            "/execute", json={"question": "irrelevant"}, headers=headers
        )

    assert response.status_code == 500
    assert (
        response.json()["detail"]
        == "Control Plane response missing runtime_compatibility"
    )


def test_runtime_control_plane_fail_closed_on_incompatible_runtime_version(
    alias_config_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tenant_keys = _load_tenant_keys()
    tenant_id = _select_tenant_id(tenant_keys)
    _, bundle_id, _ = _load_bundle_metadata()
    response_body = json.dumps(
        {
            "bundle_id": bundle_id,
            "runtime_compatibility": {"min_version": "999.0.0"},
        }
    ).encode("utf-8")

    with control_plane_server(tenant_id, 200, response_body) as base_url:
        monkeypatch.setenv("CONTRACTOR_CONTROL_PLANE_BASE_URL", base_url)
        monkeypatch.setenv("CONTRACTOR_ALIAS_CONFIG_PATH", str(alias_config_path))

        client = TestClient(app)
        headers = {"X-Tenant-Id": tenant_id, "X-Api-Key": tenant_keys[tenant_id]}

        response = client.post(
            "/execute", json={"question": "irrelevant"}, headers=headers
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Runtime incompatible with bundle"
