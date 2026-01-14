# tests/integration/test_dedicated_runtime_mode.py
from __future__ import annotations

import importlib
import os
from unittest.mock import patch

from fastapi.testclient import TestClient

# --- Environment variables MUST be set BEFORE application imports ---
TEST_API_KEY = "test-key-dedicated-runtime"
os.environ["CONTRACTOR_API_KEY"] = TEST_API_KEY
os.environ["RUNTIME_DEDICATED_TENANT_ID"] = "tenant-alpha"
# --- End of environment variable setup ---

from app.shared.config import settings as settings_module

importlib.reload(settings_module)

from app.runtime.api.main import app as runtime_app
from app.runtime.engine.ask_models import AskResponse


client = TestClient(runtime_app)


def test_dedicated_runtime_accepts_matching_tenant() -> None:
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


def test_dedicated_runtime_rejects_mismatched_tenant() -> None:
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
