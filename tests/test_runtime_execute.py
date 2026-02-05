import json
from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from app.runtime import app


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_tenant_keys() -> dict[str, str]:
    tenant_path = _repo_root() / "data" / "runtime" / "tenants.json"
    return json.loads(tenant_path.read_text(encoding="utf-8"))


def _load_golden_cases() -> list[dict[str, str]]:
    golden_path = (
        _repo_root() / "data" / "bundles" / "demo" / "faq" / "suites" / "faq_golden.json"
    )
    return json.loads(golden_path.read_text(encoding="utf-8"))


def _load_bundle_id() -> str:
    manifest_path = _repo_root() / "data" / "bundles" / "demo" / "faq" / "manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    bundle_id = manifest.get("bundle_id")
    if not bundle_id:
        raise AssertionError("Bundle id missing in manifest.yaml")
    return bundle_id


def _select_shared_tenant_id(
    tenant_keys: dict[str, str], cases: list[dict[str, str]]
) -> str:
    golden_tenants = {case.get("tenant_id") for case in cases}
    shared_tenants = sorted(set(tenant_keys.keys()) & golden_tenants)
    if not shared_tenants:
        raise AssertionError("No shared tenant_id between tenants.json and golden cases")
    return shared_tenants[0]


def _select_case_for_tenant(
    tenant_id: str, cases: list[dict[str, str]]
) -> dict[str, str]:
    for case in cases:
        if case.get("tenant_id") == tenant_id:
            return case
    raise AssertionError(f"No golden case found for tenant {tenant_id}")


def test_runtime_execute_uses_manifest_bundle_id_and_tenant_data() -> None:
    client = TestClient(app)
    tenant_keys = _load_tenant_keys()
    golden_cases = _load_golden_cases()
    tenant_id = _select_shared_tenant_id(tenant_keys, golden_cases)
    case = _select_case_for_tenant(tenant_id, golden_cases)
    bundle_id = _load_bundle_id()
    headers = {"X-Tenant-Id": tenant_id, "X-Api-Key": tenant_keys[tenant_id]}

    response = client.post("/execute", json={"question": case["question"]}, headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["bundle_id"] == bundle_id
    assert payload["tenant_id"] == tenant_id
    assert payload["intent"] == "faq_query"
    assert payload["status"] == "ok"
    assert case["expected_answer"] in payload["output_text"]
