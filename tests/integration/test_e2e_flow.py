# tests/integration/test_e2e_flow.py
from __future__ import annotations

import os
import importlib

# --- Environment variables MUST be set BEFORE application imports ---
TEST_API_KEY = "test-key-for-e2e-flow"
os.environ["CONTRACTOR_API_KEY"] = TEST_API_KEY

MOCK_POSTGRES_DSN = "postgresql://user:pass@host:5432/db"
os.environ["POSTGRES_DSN"] = MOCK_POSTGRES_DSN
# --- End of environment variable setup ---

# 1. Import the settings module itself
from app.shared.config import settings as settings_module

# 2. Reload the module to pick up the new environment variables
importlib.reload(settings_module)

# 3. Now, import the application objects. They will get the reloaded settings.
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.control_plane.api.main import app as control_plane_app
from app.control_plane.domain.bundles.validator import validate_bundle
from app.control_plane.domain.quality.reports import PromotionSetRepository, QualityReportRepository
from app.control_plane.domain.templates.safety import TemplateSafetyValidator
from app.runtime.api.main import app as runtime_app
from app.runtime.engine.context.control_plane_client import ResolveResult


def _write_quality_report(tenant_id: str, bundle_id: str) -> None:
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
    report = {
        "tenant_id": tenant_id,
        "bundle_id": bundle_id,
        "validate": validation,
        "template_safety": template_safety,
        "required_suites": required_suites,
        "suites": suite_results,
        "result": {"status": "pass", "failures": []},
        "timestamps": {"started_at": "now", "finished_at": "now"},
        "commit_hash": None,
    }
    QualityReportRepository().save(tenant_id, bundle_id, report)


def test_e2e_flow():
    control_client = TestClient(control_plane_app)
    runtime_client = TestClient(runtime_app)

    tenant_id = "demo"
    bundle_id = "202601050001"
    headers = {"X-API-Key": TEST_API_KEY}

    _write_quality_report(tenant_id, bundle_id)

    # 1. Validate the bundle (verifies control plane is up)
    response = control_client.get(
        f"/api/v1/control/tenants/{tenant_id}/bundles/{bundle_id}/validate",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pass"

    # 2. Set the 'current' alias (verifies promotion endpoint works)
    response = control_client.put(
        f"/api/v1/control/tenants/{tenant_id}/versions/current",
        headers=headers,
        json={"bundle_id": bundle_id},
    )
    assert response.status_code == 200
    assert response.json()["aliases"]["current"] == bundle_id

    # 3. Make an /ask request that uses the 'current' alias
    with patch(
        "app.runtime.engine.context.control_plane_client.ControlPlaneClient.resolve_bundle_id"
    ) as mock_resolve, patch(
        "app.runtime.engine.executor.postgres.psycopg2.connect"
    ) as mock_connect:
        # Mock the alias resolution
        mock_resolve.return_value = ResolveResult(
            bundle_id=bundle_id, url="mocked", status="ok"
        )

        # Mock the database connection and cursor
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

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["answer"] is not None
        assert response_data["meta"]["execution"]["row_count"] == 1
        assert response_data["meta"]["execution"]["results"] == [
            {"col1": "value1", "col2": "value2"}
        ]
