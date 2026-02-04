import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.runtime import app


def _load_first_golden_case() -> dict[str, str]:
    repo_root = Path(__file__).resolve().parents[1]
    golden_path = repo_root / "data" / "bundles" / "demo" / "faq" / "suites" / "faq_golden.json"
    golden_cases = json.loads(golden_path.read_text(encoding="utf-8"))
    return golden_cases[0]


def test_execute_happy_path():
    client = TestClient(app)
    case = _load_first_golden_case()
    headers = {"X-Tenant-Id": case["tenant_id"], "X-Api-Key": "test-key-a"}

    response = client.post("/execute", json={"question": case["question"]}, headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"]
    assert payload["bundle_id"] == "demo-faq-0001"
    assert payload["tenant_id"] == case["tenant_id"]
    assert payload["intent"] == "faq_query"
    assert payload["status"] == "ok"
    assert case["expected_answer"] in payload["output_text"]


def test_execute_requires_authentication():
    client = TestClient(app)
    case = _load_first_golden_case()

    response = client.post("/execute", json={"question": case["question"]})

    assert response.status_code == 401


def test_execute_is_deterministic():
    client = TestClient(app)
    case = _load_first_golden_case()
    headers = {"X-Tenant-Id": case["tenant_id"], "X-Api-Key": "test-key-a"}

    first = client.post("/execute", json={"question": case["question"]}, headers=headers)
    second = client.post("/execute", json={"question": case["question"]}, headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200

    first_payload = first.json()
    second_payload = second.json()

    assert first_payload["result"] == second_payload["result"]
