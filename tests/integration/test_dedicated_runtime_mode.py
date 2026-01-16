# tests/integration/test_dedicated_runtime_mode.py
from __future__ import annotations

import importlib
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.runtime.engine.ask_models import AskResponse


TEST_API_KEY = "test-key-dedicated-runtime"


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("CONTRACTOR_API_KEYS", TEST_API_KEY)
    monkeypatch.setenv("RUNTIME_DEDICATED_TENANT_ID", "tenant-alpha")

    for module_name in ("app.runtime.api.main", "app.runtime.api.routers.ask"):
        if module_name in sys.modules:
            del sys.modules[module_name]

    import app.shared.config.settings as settings_module

    importlib.reload(settings_module)

    from app.runtime.api.main import app as runtime_app

    return TestClient(runtime_app)


def test_dedicated_runtime_accepts_matching_tenant(client: TestClient) -> None:
    ask_payload = {"tenant_id": "tenant-alpha", "question": "ping"}
    with patch("app.runtime.api.routers.ask.prepare_ask") as mock_prepare:
        mock_prepare.return_value = (AskResponse(answer="ok", meta={}), None)

        response = client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": TEST_API_KEY},
            json=ask_payload,
        )

    assert response.status_code == 200
    assert response.json()["answer"] == "ok"
    mock_prepare.assert_called_once()


def test_dedicated_runtime_rejects_mismatched_tenant(client: TestClient) -> None:
    ask_payload = {"tenant_id": "tenant-beta", "question": "ping"}
    with patch("app.runtime.api.routers.ask.prepare_ask") as mock_prepare:
        response = client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": TEST_API_KEY},
            json=ask_payload,
        )

    assert response.status_code == 403
    assert response.json()["detail"] == {"error": "dedicated_tenant_mismatch"}
    mock_prepare.assert_not_called()


def test_dedicated_runtime_enforces_tenant_boundary(client: TestClient) -> None:
    with patch("app.runtime.api.routers.ask.prepare_ask") as mock_prepare:
        mismatch_payload = {"tenant_id": "tenant-beta", "question": "ping"}
        mismatch_response = client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": TEST_API_KEY},
            json=mismatch_payload,
        )

        assert mismatch_response.status_code == 403
        assert mismatch_response.json()["detail"] == {"error": "dedicated_tenant_mismatch"}
        mock_prepare.assert_not_called()

        mock_prepare.return_value = (AskResponse(answer="ok", meta={}), None)
        match_payload = {"tenant_id": "tenant-alpha", "question": "ping"}
        match_response = client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": TEST_API_KEY},
            json=match_payload,
        )

    assert match_response.status_code == 200
    assert match_response.json()["answer"] == "ok"
    mock_prepare.assert_called_once()
