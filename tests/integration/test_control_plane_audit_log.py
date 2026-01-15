# tests/integration/test_control_plane_audit_log.py
from __future__ import annotations

import hashlib
import importlib
import json
import sys
from typing import Any

from fastapi.testclient import TestClient

TEST_API_KEY = "test-key-for-audit-log"


def _reload_control_plane_app():
    for module_name in [
        "app.shared.config.settings",
        "app.control_plane.domain.audit.logger",
        "app.control_plane.api.routers.tenants",
        "app.control_plane.api.routers.versions",
        "app.control_plane.api.routers.bundles",
        "app.control_plane.api.routers.quality",
        "app.control_plane.api.routers.healthz",
        "app.control_plane.api.main",
    ]:
        sys.modules.pop(module_name, None)

    import app.shared.config.settings as settings_module

    importlib.reload(settings_module)

    audit_logger_module = importlib.import_module(
        "app.control_plane.domain.audit.logger"
    )
    importlib.reload(audit_logger_module)

    for module_name in [
        "app.control_plane.api.routers.tenants",
        "app.control_plane.api.routers.versions",
        "app.control_plane.api.routers.bundles",
        "app.control_plane.api.routers.quality",
        "app.control_plane.api.routers.healthz",
    ]:
        importlib.reload(importlib.import_module(module_name))

    main_module = importlib.reload(importlib.import_module("app.control_plane.api.main"))
    return main_module.create_app()


def _collect_keys(payload: Any, keys: set[str]) -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            keys.add(str(key))
            _collect_keys(value, keys)
    elif isinstance(payload, list):
        for value in payload:
            _collect_keys(value, keys)


def test_alias_change_emits_audit_log(tmp_path, monkeypatch):
    audit_path = tmp_path / "control_audit.log"
    alias_store_path = tmp_path / "tenant_aliases.json"

    monkeypatch.setenv("CONTROL_AUDIT_LOG_PATH", str(audit_path))
    monkeypatch.setenv("CONTROL_ALIAS_STORE_PATH", str(alias_store_path))
    monkeypatch.setenv("CONTRACTOR_API_KEYS", TEST_API_KEY)

    app = _reload_control_plane_app()
    client = TestClient(app)

    tenant_id = "demo"
    bundle_id = "202601050001"

    response = client.put(
        f"/api/v1/control/tenants/{tenant_id}/versions/draft",
        headers={"X-API-Key": TEST_API_KEY},
        json={"bundle_id": bundle_id},
    )
    assert response.status_code == 200

    assert audit_path.exists()
    lines = audit_path.read_text(encoding="utf-8").strip().splitlines()
    assert lines
    record = json.loads(lines[-1])

    expected_actor = (
        f"key_hash:{hashlib.sha256(TEST_API_KEY.encode('utf-8')).hexdigest()[:12]}"
    )
    assert record["action"] == "alias.set"
    assert record["tenant_id"] == tenant_id
    assert record["actor"] == expected_actor
    assert record["target"]["alias"] == "draft"
    assert record["target"]["bundle_id"] == bundle_id
    assert "ts" in record

    keys: set[str] = set()
    _collect_keys(record, keys)
    forbidden_keys = {"question", "prompt", "content", "body", "payload"}
    assert not (keys & forbidden_keys)
