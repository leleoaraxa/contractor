from __future__ import annotations

import importlib
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# --- Environment variables MUST be set BEFORE application imports ---
TEST_API_KEY = "test-key-for-promotion-gates"
os.environ["CONTRACTOR_API_KEY"] = TEST_API_KEY

MOCK_POSTGRES_DSN = "postgresql://user:pass@host:5432/db"
os.environ["POSTGRES_DSN"] = MOCK_POSTGRES_DSN
# --- End of environment variable setup ---

from app.shared.config import settings as settings_module

importlib.reload(settings_module)

from fastapi.testclient import TestClient

from app.control_plane.api.main import app as control_plane_app
from app.control_plane.domain.bundles.validator import validate_bundle
from app.control_plane.domain.quality.reports import PromotionSetRepository, QualityReportRepository
from app.control_plane.domain.templates.safety import TemplateSafetyValidator
from app.runtime.api.main import app as runtime_app
from app.shared.security import rate_limit as rate_limit_module


def _utcnow() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _write_quality_report(tenant_id: str, bundle_id: str) -> dict:
    validator = TemplateSafetyValidator()
    validation = validate_bundle(tenant_id, bundle_id)
    template_safety = validator.validate_bundle(tenant_id, bundle_id)
    required_suites = PromotionSetRepository().load(tenant_id)
    suite_results = [
        {
            "status": "pass",
            "suite_id": f"suite_{idx}",
            "suite_source": suite_path,
            "suite_path": suite_path,
            "failures": [],
        }
        for idx, suite_path in enumerate(required_suites)
    ]
    failures = []
    if validation.get("status") != "pass":
        failures.append({"type": "validation", "errors": validation.get("errors", [])})
    if template_safety.get("status") != "pass":
        failures.append({"type": "template_safety", "errors": template_safety.get("errors", [])})

    status = "pass" if not failures else "fail"
    report = {
        "tenant_id": tenant_id,
        "bundle_id": bundle_id,
        "validate": validation,
        "template_safety": template_safety,
        "required_suites": required_suites,
        "suites": suite_results,
        "result": {"status": status, "failures": failures},
        "timestamps": {"started_at": _utcnow(), "finished_at": _utcnow()},
        "commit_hash": None,
    }
    QualityReportRepository().save(tenant_id, bundle_id, report)
    return report


def _auth_headers() -> dict:
    return {"X-API-Key": TEST_API_KEY}


def test_promotion_gate_pass():
    tenant_id = "demo"
    bundle_id = "202601050001"

    _write_quality_report(tenant_id, bundle_id)

    client = TestClient(control_plane_app)
    response = client.post(
        f"/api/v1/control/tenants/{tenant_id}/aliases/candidate",
        headers=_auth_headers(),
        json={"bundle_id": bundle_id},
    )
    assert response.status_code == 200
    assert response.json()["candidate"] == bundle_id


def test_promotion_gate_fail_template_safety():
    tenant_id = "demo"
    bundle_id = "202601050002"

    report = _write_quality_report(tenant_id, bundle_id)
    assert report["template_safety"]["status"] == "fail"

    client = TestClient(control_plane_app)
    response = client.post(
        f"/api/v1/control/tenants/{tenant_id}/aliases/candidate",
        headers=_auth_headers(),
        json={"bundle_id": bundle_id},
    )
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error"] == "promotion_gate_failed"
    assert detail["gate"] == "template_safety"


def test_template_safety_gate_report(monkeypatch):
    def _run_suite_stub(*_args, **_kwargs):
        return {
            "status": "pass",
            "suite_id": "stub",
            "suite_source": "stub",
            "suite_path": "stub",
            "failures": [],
        }

    monkeypatch.setattr(
        "app.control_plane.domain.quality.service.run_suite", _run_suite_stub
    )

    client = TestClient(control_plane_app)
    response = client.post(
        "/api/v1/control/tenants/demo/bundles/202601050002/quality/run",
        headers=_auth_headers(),
        json={},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["template_safety"]["status"] == "fail"
    assert data["result"]["status"] == "fail"


def test_rate_limit_enforced():
    tenant_id = "demo"
    bundle_id = "202601050003"

    if hasattr(rate_limit_module._RL.backend, "state"):
        rate_limit_module._RL.backend.state.clear()

    runtime_client = TestClient(runtime_app)

    with patch(
        "app.runtime.engine.executor.postgres.psycopg2.connect"
    ) as mock_connect:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("value1", "value2")]
        mock_cursor.description = [("col1",), ("col2",)]
        mock_cursor.rowcount = 1

        mock_conn = mock_connect.return_value.__enter__.return_value
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        payload = {
            "tenant_id": tenant_id,
            "question": "What is the status?",
            "bundle_id": bundle_id,
            "release_alias": "current",
        }

        response1 = runtime_client.post(
            "/api/v1/runtime/ask",
            headers=_auth_headers(),
            json=payload,
        )
        response2 = runtime_client.post(
            "/api/v1/runtime/ask",
            headers=_auth_headers(),
            json=payload,
        )

    assert response1.status_code == 200
    assert response2.status_code == 429
    detail = response2.json()["detail"]
    assert detail["error"] == "rate_limit_exceeded"
