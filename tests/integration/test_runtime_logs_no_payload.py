# tests/integration/test_runtime_logs_no_payload.py
from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.runtime.engine.ask_models import AskResponse
from app.shared.logging.logger import JsonFormatter

TEST_API_KEY = "tenant-alpha:tenant_runtime_client:log-test-key"


def _build_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
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

    return TestClient(runtime_app)


def test_runtime_logs_do_not_include_payload_keys_or_values(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    client = _build_client(monkeypatch)
    ask_payload = {"tenant_id": "tenant-alpha", "question": "super-secret-payload"}

    with patch("app.runtime.api.routers.ask.prepare_ask") as mock_prepare:
        mock_prepare.return_value = (AskResponse(answer="ok", meta={}), None)
        response = client.post(
            "/api/v1/runtime/ask",
            headers={"X-API-Key": "log-test-key"},
            json=ask_payload,
        )

    assert response.status_code == 200

    logger = logging.getLogger("runtime.ask")
    caplog.set_level(logging.INFO, logger="runtime.ask")
    caplog.set_level(logging.INFO)
    caplog.handler.setFormatter(JsonFormatter())
    original_propagate = logger.propagate
    logger.propagate = True
    logger.info(
        "runtime.request payload=%s",
        {
            "question": "super-secret-payload",
            "prompt": "do-not-log",
            "content": "raw-content",
            "body": {"nested": "payload"},
            "payload": {"question": "nested-question"},
        },
    )
    record = logger.makeRecord(
        logger.name,
        logging.INFO,
        __file__,
        0,
        "runtime.request payload=%s",
        (
            {
                "question": "super-secret-payload",
                "prompt": "do-not-log",
                "content": "raw-content",
                "body": {"nested": "payload"},
                "payload": {"question": "nested-question"},
            },
        ),
        None,
    )
    caplog.handler.handle(record)
    logger.propagate = original_propagate

    output = caplog.text
    assert output

    forbidden_keys = {"question", "prompt", "content", "body", "payload"}
    for key in forbidden_keys:
        assert key not in output.lower()
    assert "super-secret-payload" not in output
