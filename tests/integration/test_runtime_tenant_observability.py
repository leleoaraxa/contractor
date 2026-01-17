# tests/integration/test_runtime_tenant_observability.py
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import patch

import hashlib
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TEST_API_KEY = "test-key-tenant-observability"

from app.runtime.engine.ask_models import AskResponse


def _build_client(
    monkeypatch: pytest.MonkeyPatch,
    *,
    raise_server_exceptions: bool = True,
) -> TestClient:
    monkeypatch.setenv("CONTRACTOR_API_KEYS", TEST_API_KEY)
    monkeypatch.setenv("RUNTIME_DEDICATED_TENANT_ID", "tenant-alpha")

    for module_name in (
        "app.runtime.api.main",
        "app.runtime.api.routers.ask",
        "app.runtime.engine.runtime_identity",
        "app.shared.config.settings",
    ):
        if module_name in sys.modules:
            del sys.modules[module_name]

    import app.shared.config.settings as settings_module

    importlib.reload(settings_module)

    from app.runtime.api.main import app as runtime_app

    return TestClient(runtime_app, raise_server_exceptions=raise_server_exceptions)


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    return _build_client(monkeypatch)


def test_runtime_metrics_include_tenant_label(client: TestClient) -> None:
    ask_payload = {"tenant_id": "tenant-alpha", "question": "ping"}
    with patch("app.runtime.api.routers.ask.prepare_ask") as mock_prepare:
        mock_prepare.return_value = (AskResponse(answer="ok", meta={}), None)
        response = client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": TEST_API_KEY},
            json=ask_payload,
        )

    assert response.status_code == 200

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    tenant_ref = hashlib.sha256("tenant-alpha".encode("utf-8")).hexdigest()
    expected = (
        f'runtime_tenant_http_requests_total{{status_code="200",tenant_ref="{tenant_ref}"}}'
    )
    assert expected in metrics_response.text


def test_runtime_metrics_record_500_status(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _build_client(monkeypatch, raise_server_exceptions=False)
    ask_payload = {"tenant_id": "tenant-alpha", "question": "ping"}
    with (
        patch("app.runtime.api.routers.ask.prepare_ask") as mock_prepare,
        patch("app.runtime.api.routers.ask.execute_prepared_ask") as mock_execute,
    ):
        mock_prepare.return_value = (None, "prep")
        mock_execute.side_effect = RuntimeError("boom")
        response = client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": TEST_API_KEY},
            json=ask_payload,
        )

    assert response.status_code == 500

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    tenant_ref = hashlib.sha256("tenant-alpha".encode("utf-8")).hexdigest()
    expected = (
        f'runtime_tenant_http_requests_total{{status_code="500",tenant_ref="{tenant_ref}"}}'
    )
    assert expected in metrics_response.text


def test_http_metrics_use_route_template_for_dynamic_paths(client: TestClient) -> None:
    request_id = "123e4567-e89b-12d3-a456-426614174000"
    with patch("app.runtime.api.routers.ask.async_queue.read_result") as mock_read_result:
        mock_read_result.return_value = {"status": "done"}
        response = client.get(
            f"/api/v1/runtime/ask/result/{request_id}",
            headers={"X-API-Key": TEST_API_KEY},
        )

    assert response.status_code == 200

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    assert request_id not in metrics_response.text
    path_template = "/api/v1/runtime/ask/result/{request_id}"
    matching_metric = None
    for line in metrics_response.text.splitlines():
        if not line.startswith("http_requests_total{"):
            continue
        labels_str = line.split("{", 1)[1].rsplit("}", 1)[0]
        labels = {}
        for item in labels_str.split(","):
            key, value = item.split("=", 1)
            labels[key] = value.strip('"')
        if (
            labels.get("service") == "runtime"
            and labels.get("method") == "GET"
            and labels.get("path") == path_template
            and labels.get("status_code") == "200"
        ):
            matching_metric = line
            break
    assert matching_metric is not None
