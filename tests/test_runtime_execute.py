import json
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from app.runtime import app


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_tenant_keys() -> dict[str, str]:
    tenant_path = _repo_root() / "data" / "runtime" / "tenants.json"
    return json.loads(tenant_path.read_text(encoding="utf-8"))


def _load_bundle_id() -> str:
    manifest_path = _repo_root() / "data" / "bundles" / "demo" / "faq" / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    return str(manifest.get("bundle_id"))


def _load_golden_cases() -> list[dict[str, str]]:
    golden_path = _repo_root() / "data" / "bundles" / "demo" / "faq" / "suites" / "faq_golden.json"
    return json.loads(golden_path.read_text(encoding="utf-8"))


def _select_case_for_tenant(
    tenant_id: str, cases: list[dict[str, str]]
) -> dict[str, str]:
    for case in cases:
        if case.get("tenant_id") == tenant_id:
            return case
    raise AssertionError(f"No golden case found for tenant {tenant_id}")


def test_execute_happy_path():
    client = TestClient(app)
    tenant_keys = _load_tenant_keys()
    tenant_id = sorted(tenant_keys.keys())[0]
    case = _select_case_for_tenant(tenant_id, _load_golden_cases())
    headers = {"X-Tenant-Id": tenant_id, "X-Api-Key": tenant_keys[tenant_id]}

    response = client.post("/execute", json={"question": case["question"]}, headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"]
    assert payload["bundle_id"] == _load_bundle_id()
    assert payload["tenant_id"] == tenant_id
    assert payload["intent"] == "faq_query"
    assert payload["status"] == "ok"
    assert case["expected_answer"] in payload["output_text"]


def test_execute_requires_authentication():
    client = TestClient(app)
    case = _load_golden_cases()[0]

    response = client.post("/execute", json={"question": case["question"]})

    assert response.status_code == 401


def test_execute_is_deterministic():
    client = TestClient(app)
    tenant_keys = _load_tenant_keys()
    tenant_id = sorted(tenant_keys.keys())[0]
    case = _select_case_for_tenant(tenant_id, _load_golden_cases())
    headers = {"X-Tenant-Id": tenant_id, "X-Api-Key": tenant_keys[tenant_id]}

    first = client.post("/execute", json={"question": case["question"]}, headers=headers)
    second = client.post("/execute", json={"question": case["question"]}, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200

    first_payload = first.json()
    second_payload = second.json()

    assert first_payload["result"] == second_payload["result"]
