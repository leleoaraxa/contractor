import hashlib
import json
import shutil
import tarfile
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from app import runtime


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _source_bundle_path() -> Path:
    return _repo_root() / "data" / "bundles" / "demo" / "faq"


def _bundle_id() -> str:
    manifest = yaml.safe_load((_source_bundle_path() / "manifest.yaml").read_text(encoding="utf-8"))
    return str(manifest["bundle_id"])


def _make_bundle_tarball(tmp_path: Path, bundle_id: str) -> tuple[Path, str]:
    archive = tmp_path / f"{bundle_id}.tar.gz"
    with tarfile.open(archive, mode="w:gz") as tar:
        tar.add(_source_bundle_path(), arcname=bundle_id)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    return archive, digest


def _runtime_headers(request_id: str = "rid-0017") -> dict[str, str]:
    return {
        "X-Tenant-Id": "tenant_a",
        "X-Api-Key": "runtime_test_key_a",
        "X-Request-Id": request_id,
    }


@contextmanager
def _control_plane_server(
    tenant_id: str,
    payload: dict[str, object],
    status_code: int = 200,
) -> Iterator[str]:
    body = json.dumps(payload).encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            expected_path = f"/tenants/{tenant_id}/resolve/current"
            if self.path != expected_path:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

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


@contextmanager
def _origin_server(directory: Path) -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            requested = self.path.lstrip("/")
            archive_path = directory / requested
            if not archive_path.exists():
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/gzip")
            self.end_headers()
            self.wfile.write(archive_path.read_bytes())

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
def runtime_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    runtime.RATE_LIMIT_COUNTERS.clear()
    monkeypatch.setenv(
        "CONTRACTOR_AUDIT_CONFIG_JSON",
        json.dumps({"enabled": True, "sink": "stdout", "retention_days": 7}),
    )
    monkeypatch.setenv(
        "CONTRACTOR_TENANT_KEYS", json.dumps({"tenant_a": "runtime_test_key_a"})
    )
    monkeypatch.setenv(
        "CONTRACTOR_RATE_LIMIT_POLICY_JSON",
        json.dumps(
            {
                "rate_limit": {"window_seconds": 60, "max_requests": 100},
                "quota": {"window_seconds": 86400, "max_requests": 100},
                "tenants": {
                    "*": {
                        "rate_limit": {"window_seconds": 60, "max_requests": 100},
                        "quota": {"window_seconds": 86400, "max_requests": 100},
                    }
                },
            }
        ),
    )
    bundle_root = tmp_path / "data" / "bundles"
    bundle_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(runtime, "_bundle_root", lambda: bundle_root)
    return TestClient(runtime.app)


def test_bundle_cache_hit(
    runtime_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    bundle_id = _bundle_id()
    target = tmp_path / "data" / "bundles" / bundle_id
    shutil.copytree(_source_bundle_path(), target)
    cp_payload = {
        "bundle_id": bundle_id,
        "runtime_compatibility": {"min_version": "0.0.0"},
    }

    with _control_plane_server("tenant_a", cp_payload) as cp_base:
        monkeypatch.setenv("CONTRACTOR_CONTROL_PLANE_BASE_URL", cp_base)
        response = runtime_client.post(
            "/execute",
            json={"question": "O que é o CONTRACTOR?"},
            headers=_runtime_headers("rid-hit"),
        )
    captured = capsys.readouterr().out

    assert response.status_code == 200
    events = [json.loads(line) for line in captured.splitlines() if line.strip()]
    runtime_event = [e for e in events if e.get("service") == "runtime"][0]
    assert runtime_event["bundle_cache"] == {"status": "hit", "bundle_id": bundle_id}


def test_bundle_cache_miss_download_unpack_execute(
    runtime_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    bundle_id = _bundle_id()
    archive, digest = _make_bundle_tarball(tmp_path, bundle_id)
    cp_payload = {
        "bundle_id": bundle_id,
        "bundle_sha256": digest,
        "runtime_compatibility": {"min_version": "0.0.0"},
    }

    with _origin_server(archive.parent) as origin_base:
        with _control_plane_server("tenant_a", cp_payload) as cp_base:
            monkeypatch.setenv("CONTRACTOR_CONTROL_PLANE_BASE_URL", cp_base)
            monkeypatch.setenv("CONTRACTOR_BUNDLE_BASE_URL", origin_base)
            response = runtime_client.post(
                "/execute",
                json={"question": "O que é o CONTRACTOR?"},
                headers=_runtime_headers("rid-miss"),
            )

    assert response.status_code == 200
    assert (tmp_path / "data" / "bundles" / bundle_id / "manifest.yaml").exists()


def test_bundle_digest_invalid_returns_500(
    runtime_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    bundle_id = _bundle_id()
    archive, _ = _make_bundle_tarball(tmp_path, bundle_id)
    cp_payload = {
        "bundle_id": bundle_id,
        "bundle_sha256": "0" * 64,
        "runtime_compatibility": {"min_version": "0.0.0"},
    }

    with _origin_server(archive.parent) as origin_base:
        with _control_plane_server("tenant_a", cp_payload) as cp_base:
            monkeypatch.setenv("CONTRACTOR_CONTROL_PLANE_BASE_URL", cp_base)
            monkeypatch.setenv("CONTRACTOR_BUNDLE_BASE_URL", origin_base)
            response = runtime_client.post(
                "/execute",
                json={"question": "irrelevant"},
                headers=_runtime_headers("rid-digest"),
            )

    assert response.status_code == 500
    assert response.json()["detail"] == "Bundle digest mismatch"


def test_bundle_structure_invalid_returns_500(
    runtime_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    bundle_id = _bundle_id()
    bad_bundle = tmp_path / bundle_id
    bad_bundle.mkdir(parents=True, exist_ok=True)
    (bad_bundle / "manifest.yaml").write_text("bundle_id: demo\n", encoding="utf-8")
    archive = tmp_path / f"{bundle_id}.tar.gz"
    with tarfile.open(archive, mode="w:gz") as tar:
        tar.add(bad_bundle, arcname=bundle_id)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()

    cp_payload = {
        "bundle_id": bundle_id,
        "bundle_sha256": digest,
        "runtime_compatibility": {"min_version": "0.0.0"},
    }

    with _origin_server(archive.parent) as origin_base:
        with _control_plane_server("tenant_a", cp_payload) as cp_base:
            monkeypatch.setenv("CONTRACTOR_CONTROL_PLANE_BASE_URL", cp_base)
            monkeypatch.setenv("CONTRACTOR_BUNDLE_BASE_URL", origin_base)
            response = runtime_client.post(
                "/execute",
                json={"question": "irrelevant"},
                headers=_runtime_headers("rid-struct"),
            )

    assert response.status_code == 500
    assert response.json()["detail"] == "Bundle structure invalid"


def test_bundle_not_found_in_origin_returns_503(
    runtime_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    bundle_id = _bundle_id()
    cp_payload = {
        "bundle_id": bundle_id,
        "bundle_sha256": "f" * 64,
        "runtime_compatibility": {"min_version": "0.0.0"},
    }

    with _origin_server(tmp_path) as origin_base:
        with _control_plane_server("tenant_a", cp_payload) as cp_base:
            monkeypatch.setenv("CONTRACTOR_CONTROL_PLANE_BASE_URL", cp_base)
            monkeypatch.setenv("CONTRACTOR_BUNDLE_BASE_URL", origin_base)
            response = runtime_client.post(
                "/execute",
                json={"question": "irrelevant"},
                headers=_runtime_headers("rid-missing"),
            )

    assert response.status_code == 503
    assert response.json()["detail"] == "Bundle not found in origin"
