import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient

from app.runtime import app


class ControlPlaneState:
    def __init__(self) -> None:
        self.call_count = 0
        self.last_tenant_id: str | None = None
        self.responses: dict[str, dict[str, object]] = {}


def _load_first_golden_case() -> dict[str, str]:
    repo_root = Path(__file__).resolve().parents[2]
    golden_path = (
        repo_root / "data" / "bundles" / "demo" / "faq" / "suites" / "faq_golden.json"
    )
    golden_cases = json.loads(golden_path.read_text(encoding="utf-8"))
    return golden_cases[0]


def _make_control_plane_handler(state: ControlPlaneState) -> type[BaseHTTPRequestHandler]:
    class ControlPlaneHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path.startswith("/tenants/") and parsed.path.endswith("/resolve/current"):
                _, tenant_id, *_ = parsed.path.strip("/").split("/")
                state.call_count += 1
                state.last_tenant_id = tenant_id
                response = state.responses.get(
                    tenant_id, {"status": 404, "body": {"detail": "not found"}}
                )
                status_code = int(response.get("status", 500))
                body = response.get("body", {})
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(body).encode("utf-8"))
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return

    return ControlPlaneHandler


@pytest.fixture
def control_plane_server() -> tuple[ControlPlaneState, str]:
    state = ControlPlaneState()
    server = ThreadingHTTPServer(("127.0.0.1", 0), _make_control_plane_handler(state))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        yield state, base_url
    finally:
        server.shutdown()
        thread.join(timeout=1)


def test_runtime_e2e_resolves_current_and_executes_demo(
    control_plane_server: tuple[ControlPlaneState, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, base_url = control_plane_server
    state.responses["tenant_a"] = {
        "status": 200,
        "body": {"bundle_id": "demo-faq-0001"},
    }
    monkeypatch.setenv("CONTRACTOR_CONTROL_PLANE_BASE_URL", base_url)

    client = TestClient(app)
    case = _load_first_golden_case()
    headers = {"X-Tenant-Id": case["tenant_id"], "X-Api-Key": "test-key-a"}

    response = client.post("/execute", json={"question": case["question"]}, headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert state.call_count == 1
    assert state.last_tenant_id == case["tenant_id"]
    assert payload["bundle_id"] == "demo-faq-0001"
    assert payload["intent"] == "faq_query"
    assert payload["status"] == "ok"
    assert case["expected_answer"] in payload["output_text"]


def test_runtime_e2e_fail_closed_when_control_plane_errors(
    control_plane_server: tuple[ControlPlaneState, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state, base_url = control_plane_server
    state.responses["tenant_a"] = {
        "status": 500,
        "body": {"detail": "boom"},
    }
    monkeypatch.setenv("CONTRACTOR_CONTROL_PLANE_BASE_URL", base_url)

    client = TestClient(app)
    case = _load_first_golden_case()
    headers = {"X-Tenant-Id": case["tenant_id"], "X-Api-Key": "test-key-a"}

    response = client.post("/execute", json={"question": case["question"]}, headers=headers)

    assert response.status_code == 500
    assert "Control Plane error" in response.json()["detail"]
