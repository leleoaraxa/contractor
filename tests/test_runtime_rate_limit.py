# tests/test_runtime_rate_limit.py
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.runtime as runtime

QUESTION = "O que é um bundle no CONTRACTOR?"
TENANT_ID = "tenant_a"
API_KEY = "runtime-test-key"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    runtime.RATE_LIMIT_COUNTERS.clear()
    monkeypatch.setenv("CONTRACTOR_TENANT_KEYS", json.dumps({TENANT_ID: API_KEY}))
    monkeypatch.delenv("CONTRACTOR_RATE_LIMIT_POLICY_PATH", raising=False)
    monkeypatch.delenv("CONTRACTOR_RATE_LIMIT_POLICY_JSON", raising=False)
    return TestClient(runtime.app)


def _headers() -> dict[str, str]:
    return {"X-Tenant-Id": TENANT_ID, "X-Api-Key": API_KEY}


def _set_policy(monkeypatch: pytest.MonkeyPatch, policy: dict[str, object]) -> None:
    monkeypatch.setenv("CONTRACTOR_RATE_LIMIT_POLICY_JSON", json.dumps(policy))


def _base_policy(*, rate_limit_max: int, quota_max: int) -> dict[str, object]:
    return {
        "rate_limit": {"window_seconds": 60, "max_requests": 1000},
        "quota": {"window_seconds": 86400, "max_requests": 1000},
        "tenants": {
            "*": {
                "rate_limit": {"window_seconds": 60, "max_requests": 1000},
                "quota": {"window_seconds": 86400, "max_requests": 1000},
            },
            TENANT_ID: {
                "rate_limit": {"window_seconds": 60, "max_requests": rate_limit_max},
                "quota": {"window_seconds": 86400, "max_requests": quota_max},
            },
        },
    }


def test_runtime_execute_fails_closed_when_policy_path_missing(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("CONTRACTOR_RATE_LIMIT_POLICY_JSON", raising=False)
    missing_path = tmp_path / "missing-policy.yaml"
    monkeypatch.setenv("CONTRACTOR_RATE_LIMIT_POLICY_PATH", str(missing_path))

    response = client.post("/execute", json={"question": QUESTION}, headers=_headers())

    assert response.status_code == 500


def test_runtime_execute_fails_closed_when_policy_env_json_invalid(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CONTRACTOR_RATE_LIMIT_POLICY_JSON", "{invalid")

    response = client.post("/execute", json={"question": QUESTION}, headers=_headers())

    assert response.status_code == 500


def test_runtime_execute_happy_path_within_limits(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_policy(monkeypatch, _base_policy(rate_limit_max=2, quota_max=3))
    monkeypatch.setattr(runtime.time, "time", lambda: 1700000000)

    response = client.post("/execute", json={"question": QUESTION}, headers=_headers())

    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "2"
    assert response.headers["X-RateLimit-Remaining"] == "1"
    assert response.headers["X-RateLimit-Reset"] == "1700000040"


def test_runtime_execute_rejects_when_rate_limit_exceeded(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_policy(monkeypatch, _base_policy(rate_limit_max=1, quota_max=10))
    monkeypatch.setattr(runtime.time, "time", lambda: 1700000000)

    first = client.post("/execute", json={"question": QUESTION}, headers=_headers())
    second = client.post("/execute", json={"question": QUESTION}, headers=_headers())

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["detail"] == "Rate limit exceeded"
    assert int(second.headers["Retry-After"]) > 0


def test_runtime_execute_rejects_when_quota_exceeded(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    _set_policy(monkeypatch, _base_policy(rate_limit_max=10, quota_max=1))
    monkeypatch.setattr(runtime.time, "time", lambda: 1700000000)

    first = client.post("/execute", json={"question": QUESTION}, headers=_headers())
    second = client.post("/execute", json={"question": QUESTION}, headers=_headers())

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["detail"] == "Quota exceeded"
    assert int(second.headers["Retry-After"]) > 0
