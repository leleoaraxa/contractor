# tests/test_audit_end_to_end.py
from __future__ import annotations

import json
import shutil
import threading
from contextlib import contextmanager
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app import control_plane, runtime
from app.audit import audit_emit


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _bundle_path() -> Path:
    return _repo_root() / "data" / "bundles" / "demo" / "faq"


def _runtime_headers(request_id: str | None = None) -> dict[str, str]:
    headers = {
        "X-Tenant-Id": "tenant_a",
        "X-Api-Key": "runtime_test_key_a",
    }
    if request_id:
        headers["X-Request-Id"] = request_id
    return headers


def _runtime_audit_lines(captured: str) -> list[dict[str, Any]]:
    lines = [line for line in captured.splitlines() if line.strip()]
    events = [json.loads(line) for line in lines]
    return [e for e in events if e.get("service") == "runtime"]


def _prepare_bundle_cache_hit(tmp_path: Path, bundle_id: str) -> Path:
    source = _bundle_path()
    bundle_root = tmp_path / "bundles"
    target = bundle_root / bundle_id
    shutil.copytree(source, target)
    return bundle_root


def _control_plane_audit_lines(captured: str) -> list[dict[str, Any]]:
    lines = [line for line in captured.splitlines() if line.strip()]
    events = [json.loads(line) for line in lines]
    return [e for e in events if e.get("service") == "control_plane"]


@pytest.fixture
def runtime_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    runtime.RATE_LIMIT_COUNTERS.clear()
    monkeypatch.setenv(
        "CONTRACTOR_AUDIT_CONFIG_JSON",
        json.dumps(
            {
                "enabled": True,
                "sink": "stdout",
                "file_path": "data/audit/audit.log.jsonl",
                "retention_days": 7,
            }
        ),
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
                    },
                    "tenant_a": {
                        "rate_limit": {"window_seconds": 60, "max_requests": 100},
                        "quota": {"window_seconds": 86400, "max_requests": 100},
                    },
                },
            }
        ),
    )
    monkeypatch.delenv("CONTRACTOR_CONTROL_PLANE_BASE_URL", raising=False)
    return TestClient(runtime.app)


@pytest.fixture
def control_plane_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv(
        "CONTRACTOR_AUDIT_CONFIG_JSON",
        json.dumps(
            {
                "enabled": True,
                "sink": "stdout",
                "file_path": "data/audit/audit.log.jsonl",
                "retention_days": 7,
            }
        ),
    )
    monkeypatch.setenv(
        control_plane.AUTH_CONFIG_JSON_ENV,
        json.dumps({"tenants": {"tenant_a": {"token": "cp_test_key_a"}}}),
    )
    monkeypatch.setenv(
        control_plane.ALIAS_CONFIG_PATH_ENV,
        str(_repo_root() / "data" / "control_plane" / "demo_aliases.json"),
    )
    return TestClient(control_plane.app)


def test_runtime_audit_happy_path_stdout(
    runtime_client: TestClient,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runtime, "now_utc_iso", lambda: "2026-02-05T13:45:12Z")
    response = runtime_client.post(
        "/execute",
        json={"question": "O que é o CONTRACTOR?"},
        headers=_runtime_headers("rid-happy"),
    )
    captured = capsys.readouterr().out

    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"]
    assert response.headers["X-RateLimit-Remaining"]
    assert response.headers["X-RateLimit-Reset"]

    events = _runtime_audit_lines(captured)
    assert len(events) == 1
    event = events[0]
    assert event["service"] == "runtime"
    assert event["event"] == "execute"
    assert event["outcome"] == "ok"
    assert event["request_id"] == "rid-happy"
    assert event["question_sha256"] == (
        "c959a358f53a82ae5c47bd762af09461825e835700c5fe8722b9d4e2dd925f35"
    )
    assert "Authorization" not in captured
    assert "X-Api-Key" not in captured


def test_runtime_audit_auth_errors_emit_event(
    runtime_client: TestClient,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runtime, "now_utc_iso", lambda: "2026-02-05T13:45:12Z")

    response_401 = runtime_client.post("/execute", json={"question": "hello"})
    response_403 = runtime_client.post(
        "/execute",
        json={"question": "hello"},
        headers={"X-Tenant-Id": "tenant_a", "X-Api-Key": "wrong"},
    )
    captured = capsys.readouterr().out

    assert response_401.status_code == 401
    assert response_403.status_code == 403

    events = _runtime_audit_lines(captured)
    assert len(events) == 2
    assert events[0]["outcome"] == "error"
    assert events[0]["http_status"] == 401
    assert events[1]["outcome"] == "error"
    assert events[1]["http_status"] == 403
    assert "Authorization" not in captured
    assert "X-Api-Key" not in captured


@contextmanager
def _capture_runtime_request_id_server(
    tenant_id: str, bundle_id: str, min_version: str
) -> Any:
    observed: dict[str, str | None] = {"x_request_id": None}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            expected = f"/tenants/{tenant_id}/resolve/current"
            if self.path != expected:
                self.send_response(404)
                self.end_headers()
                return
            observed["x_request_id"] = self.headers.get("X-Request-Id")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(
                json.dumps(
                    {
                        "bundle_id": bundle_id,
                        "runtime_compatibility": {"min_version": min_version},
                    }
                ).encode("utf-8")
            )

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}", observed
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


def test_runtime_propagates_x_request_id_to_control_plane(
    runtime_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    bundle_path = _bundle_path()
    alias_path = tmp_path / "aliases.json"
    alias_path.write_text(
        json.dumps(
            {
                "tenants": {
                    "*": {
                        "current_bundle_path": str(bundle_path),
                        "bundle_id": "demo-faq-0001",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("CONTRACTOR_ALIAS_CONFIG_PATH", str(alias_path))
    bundle_root = _prepare_bundle_cache_hit(tmp_path, "demo-faq-0001")
    monkeypatch.setattr(runtime, "_bundle_root", lambda: bundle_root)

    with _capture_runtime_request_id_server("tenant_a", "demo-faq-0001", "0.0.0") as (
        base_url,
        observed,
    ):
        monkeypatch.setenv("CONTRACTOR_CONTROL_PLANE_BASE_URL", base_url)
        response = runtime_client.post(
            "/execute",
            json={"question": "O que é o CONTRACTOR?"},
            headers=_runtime_headers("rid-propagate"),
        )

    assert response.status_code == 200
    assert observed["x_request_id"] == "rid-propagate"


def test_control_plane_audit_ok_and_unauthorized(
    control_plane_client: TestClient,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(control_plane, "now_utc_iso", lambda: "2026-02-05T13:45:12Z")

    response_ok = control_plane_client.get(
        "/tenants/tenant_a/resolve/current",
        headers={
            "Authorization": "Bearer cp_test_key_a",
            "X-Tenant-Id": "tenant_a",
            "X-Request-Id": "cp-rid",
        },
    )
    response_401 = control_plane_client.get(
        "/tenants/tenant_a/resolve/current",
        headers={"X-Tenant-Id": "tenant_a"},
    )
    captured = capsys.readouterr().out

    assert response_ok.status_code == 200
    assert response_401.status_code == 401

    events = _control_plane_audit_lines(captured)
    assert len(events) == 2
    assert events[0]["service"] == "control_plane"
    assert events[0]["event"] == "resolve_current"
    assert events[0]["outcome"] == "ok"
    assert events[0]["request_id"] == "cp-rid"
    assert events[1]["http_status"] == 401
    assert "Authorization" not in captured


def test_audit_file_sink_rotation_and_retention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    audit_base = tmp_path / "audit.log.jsonl"
    monkeypatch.setenv(
        "CONTRACTOR_AUDIT_CONFIG_JSON",
        json.dumps(
            {
                "enabled": True,
                "sink": "file",
                "file_path": str(audit_base),
                "retention_days": 7,
            }
        ),
    )

    old_file = tmp_path / "audit-2026-01-01.log.jsonl"
    old_file.write_text("{}\n", encoding="utf-8")

    event = {
        "ts_utc": "2026-02-05T13:45:12Z",
        "service": "runtime",
        "event": "execute",
        "tenant_id": "tenant_a",
        "request_id": "rid",
        "actor": "external_client",
        "outcome": "ok",
        "http_status": 200,
        "latency_ms": 1,
    }

    monkeypatch.setattr("app.audit.now_utc", lambda: datetime(2026, 2, 5, tzinfo=UTC))
    audit_emit(event)

    current_file = tmp_path / "audit-2026-02-05.log.jsonl"
    assert current_file.exists()
    assert not old_file.exists()
