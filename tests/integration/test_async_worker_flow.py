# tests/integration/test_async_worker_flow.py
from __future__ import annotations

import importlib
import os
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

# --- Environment variables MUST be set BEFORE application imports ---
TEST_API_KEY = "test-key-for-async"
os.environ["CONTRACTOR_API_KEY"] = TEST_API_KEY
os.environ["POSTGRES_DSN"] = "postgresql://user:pass@host:5432/db"
# --- End of environment variable setup ---

from app.shared.config import settings as settings_module

importlib.reload(settings_module)

from app.runtime.api.main import app as runtime_app
from app.runtime.engine.ask_handler import handle_ask
from app.runtime.engine.ask_models import AskRequest
from app.runtime.engine.context.control_plane_client import ResolveResult
from app.runtime.worker import queue as queue_module


def test_async_flow_returns_result():
    runtime_client = TestClient(runtime_app)
    headers = {"X-API-Key": TEST_API_KEY, "X-Async": "1"}

    tenant_id = "demo"
    bundle_id = "202601050001"

    pending_ids: set[str] = set()
    results: dict[str, dict] = {}

    def fake_enqueue_job(request_id: str, payload: dict, ttl_s: int) -> None:
        pending_ids.add(request_id)

    def fake_read_result(request_id: str):
        if request_id in results:
            return results[request_id]
        if request_id in pending_ids:
            raise queue_module.ResultNotReady()
        raise queue_module.ResultExpired()

    def fake_write_result(request_id: str, result_payload: dict, ttl_s: int | None = None) -> None:
        pending_ids.discard(request_id)
        results[request_id] = result_payload

    with patch(
        "app.runtime.engine.context.control_plane_client.ControlPlaneClient.resolve_bundle_id"
    ) as mock_resolve, patch(
        "app.runtime.engine.executor.postgres.psycopg2.connect"
    ) as mock_connect, patch(
        "app.runtime.worker.queue.is_available",
        return_value=True,
    ), patch(
        "app.runtime.worker.queue.enqueue_job",
        side_effect=fake_enqueue_job,
    ), patch(
        "app.runtime.worker.queue.read_result",
        side_effect=fake_read_result,
    ), patch(
        "app.runtime.worker.queue.write_result",
        side_effect=fake_write_result,
    ):
        mock_resolve.return_value = ResolveResult(bundle_id=bundle_id, url="mocked", status="ok")

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("value1", "value2")]
        mock_cursor.description = [("col1",), ("col2",)]
        mock_cursor.rowcount = 1

        mock_conn = mock_connect.return_value.__enter__.return_value
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        ask_payload = {
            "tenant_id": tenant_id,
            "question": "What is the status?",
            "release_alias": "current",
        }
        response = runtime_client.post(
            "/api/v1/runtime/ask",
            headers=headers,
            json=ask_payload,
        )

        assert response.status_code == 202
        request_id = response.json()["request_id"]
        assert request_id in pending_ids

        pending_response = runtime_client.get(
            f"/api/v1/runtime/ask/result/{request_id}",
            headers={"X-API-Key": TEST_API_KEY},
        )
        assert pending_response.status_code == 404
        assert pending_response.json()["detail"]["error"] == "not_ready"

        result = handle_ask(AskRequest(**ask_payload), explain_enabled=False)
        fake_write_result(request_id, result.model_dump())

        final_response = runtime_client.get(
            f"/api/v1/runtime/ask/result/{request_id}",
            headers={"X-API-Key": TEST_API_KEY},
        )
        assert final_response.status_code == 200
        final_payload = final_response.json()
        assert final_payload["answer"] is not None
        assert final_payload["meta"]["execution"]["row_count"] == 1
