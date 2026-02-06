from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, Header, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.audit import AuditConfigError, audit_emit, now_utc_iso
from app.runtime import RuntimeConfigError, load_tenant_keys
from app.runtime import app as runtime_app

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALIAS_PATH = REPO_ROOT / "data" / "control_plane" / "demo_aliases.json"
DEFAULT_TENANT_AUTH_PATH = REPO_ROOT / "data" / "control_plane" / "tenants.json"

AUTH_CONFIG_PATH_ENV = "CONTRACTOR_CONTROL_PLANE_TENANT_AUTH_CONFIG_PATH"
AUTH_CONFIG_JSON_ENV = "CONTRACTOR_CONTROL_PLANE_TENANT_AUTH_CONFIG_JSON"
ALIAS_CONFIG_PATH_ENV = "CONTRACTOR_CONTROL_PLANE_ALIAS_CONFIG_PATH"

app = FastAPI()
GATE_HISTORY_LIMIT = 50
GATE_STORAGE_ROOT = REPO_ROOT / "data" / "control_plane" / "gates"


class GateRunRequest(BaseModel):
    suite_id: str | None = None


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp_path.replace(path)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_bundle_path_by_bundle_id(bundle_id: str) -> Path:
    bundle_root = REPO_ROOT / "data" / "bundles"
    for manifest_path in sorted(bundle_root.glob("**/manifest.yaml")):
        manifest = _load_yaml_file(manifest_path)
        if manifest.get("bundle_id") == bundle_id:
            return manifest_path.parent
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bundle not found")


def _list_suite_paths(bundle_path: Path, suite_id: str | None) -> list[Path]:
    suites_dir = bundle_path / "suites"
    if not suites_dir.exists() or not suites_dir.is_dir():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bundle suites missing",
        )
    if suite_id:
        suite_path = suites_dir / f"{suite_id}.json"
        if not suite_path.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suite not found")
        return [suite_path]

    suite_paths = sorted(suites_dir.glob("*.json"))
    if not suite_paths:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bundle suites missing",
        )
    return suite_paths


def _load_and_validate_suite(path: Path) -> list[dict[str, str]]:
    try:
        suite_data = _read_json(path)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Suite invalid",
        ) from exc

    if not isinstance(suite_data, list) or not suite_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Suite invalid",
        )

    normalized: list[dict[str, str]] = []
    for case in suite_data:
        if not isinstance(case, dict):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Suite invalid",
            )
        tenant_id = case.get("tenant_id")
        question = case.get("question")
        expected_answer = case.get("expected_answer")
        if (
            not isinstance(tenant_id, str)
            or not tenant_id
            or not isinstance(question, str)
            or not question
            or not isinstance(expected_answer, str)
            or not expected_answer
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Suite invalid",
            )
        normalized.append(
            {
                "tenant_id": tenant_id,
                "question": question,
                "expected_answer": expected_answer,
            }
        )
    return normalized


def _gate_storage_file(tenant_id: str, bundle_id: str, gate_id: str) -> Path:
    return GATE_STORAGE_ROOT / tenant_id / bundle_id / f"{gate_id}.json"


def _load_gate_result(tenant_id: str, bundle_id: str, gate_id: str) -> dict[str, Any]:
    path = _gate_storage_file(tenant_id, bundle_id, gate_id)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gate not found")
    try:
        payload = _read_json(path)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gate storage invalid",
        ) from exc
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Gate storage invalid",
        )
    return payload


def _run_suite_cases(
    suite_cases: list[dict[str, str]], request_id: str
) -> tuple[list[dict[str, Any]], int, int]:
    runtime_client = TestClient(runtime_app)
    tenant_keys = load_tenant_keys()
    results: list[dict[str, Any]] = []
    passed_count = 0

    for index, case in enumerate(suite_cases):
        tenant_id = case["tenant_id"]
        api_key = tenant_keys.get(tenant_id)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Runtime tenant key missing",
            )
        internal_request_id = f"{request_id}:case:{index}"
        response = runtime_client.post(
            "/execute",
            json={"question": case["question"]},
            headers={
                "X-Tenant-Id": tenant_id,
                "X-Api-Key": api_key,
                "X-Request-Id": internal_request_id,
            },
        )
        if response.status_code >= 500:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Runtime execution failure",
            )
        if response.status_code != status.HTTP_200_OK:
            passed = False
        else:
            body = response.json()
            result = body.get("result")
            answer = result.get("answer") if isinstance(result, dict) else None
            passed = isinstance(answer, str) and answer == case["expected_answer"]
        if passed:
            passed_count += 1
        results.append(
            {
                "case_index": index,
                "tenant_id": tenant_id,
                "request_id": internal_request_id,
                "outcome": "pass" if passed else "fail",
                "http_status": int(response.status_code),
            }
        )
    total = len(suite_cases)
    return results, passed_count, total - passed_count


def _ensure_suite_matches_tenant(suite_cases: list[dict[str, str]], tenant_id: str) -> None:
    if any(case["tenant_id"] != tenant_id for case in suite_cases):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Suite invalid",
        )


class AuthConfigError(RuntimeError):
    """Raised when tenant auth configuration is unavailable or invalid."""


def _load_json_file(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml_file(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_alias_config() -> dict[str, Any]:
    env_path = os.getenv(ALIAS_CONFIG_PATH_ENV)
    alias_path = Path(env_path) if env_path else DEFAULT_ALIAS_PATH
    try:
        return _load_json_file(alias_path)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _load_tenant_auth_config_payload() -> dict[str, Any]:
    env_json = os.getenv(AUTH_CONFIG_JSON_ENV)
    if env_json:
        try:
            return json.loads(env_json)
        except json.JSONDecodeError as exc:
            raise AuthConfigError("Invalid tenant auth config JSON in environment") from exc

    env_path = os.getenv(AUTH_CONFIG_PATH_ENV)
    auth_path = Path(env_path) if env_path else DEFAULT_TENANT_AUTH_PATH
    try:
        return _load_json_file(auth_path)
    except FileNotFoundError as exc:
        raise AuthConfigError("Tenant auth config file is missing") from exc
    except json.JSONDecodeError as exc:
        raise AuthConfigError("Tenant auth config file has invalid JSON") from exc


def load_tenant_token_index() -> dict[str, str]:
    config = _load_tenant_auth_config_payload()
    tenants = config.get("tenants") if isinstance(config, dict) else None
    if not isinstance(tenants, dict) or not tenants:
        raise AuthConfigError("Tenant auth config must define a non-empty tenants object")

    token_to_tenant: dict[str, str] = {}
    for tenant_id, tenant_cfg in tenants.items():
        if not isinstance(tenant_id, str) or not tenant_id:
            raise AuthConfigError("Tenant auth config has invalid tenant_id")
        if not isinstance(tenant_cfg, dict):
            raise AuthConfigError("Tenant auth config tenant entry must be an object")
        token = tenant_cfg.get("token")
        if not isinstance(token, str) or not token:
            raise AuthConfigError("Tenant auth config token must be a non-empty string")
        if token in token_to_tenant:
            raise AuthConfigError("Tenant auth config token must map to exactly one tenant")
        token_to_tenant[token] = tenant_id

    return token_to_tenant


def _extract_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization",
        )
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0] != "Bearer" or not parts[1]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed Authorization",
        )
    return parts[1]


def enforce_control_plane_auth(
    tenant_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
) -> str:
    token = _extract_bearer_token(authorization)
    if not x_tenant_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing X-Tenant-Id")

    try:
        token_to_tenant = load_tenant_token_index()
    except AuthConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    token_tenant_id = token_to_tenant.get(token)
    if token_tenant_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if token_tenant_id != x_tenant_id or tenant_id != x_tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return token_tenant_id


def resolve_current_bundle_metadata(tenant_id: str) -> tuple[str, str, str | None]:
    config = load_alias_config()
    tenants = config.get("tenants", config)
    tenant_entry = tenants.get(tenant_id) or tenants.get("*")
    if not tenant_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    bundle_sha256: str | None = None
    if isinstance(tenant_entry, str):
        bundle_path_value = tenant_entry
        bundle_id = None
    else:
        bundle_path_value = tenant_entry.get("current_bundle_path") or tenant_entry.get(
            "bundle_path"
        )
        bundle_id = tenant_entry.get("bundle_id")
        raw_digest = tenant_entry.get("bundle_sha256")
        if raw_digest is not None:
            if not isinstance(raw_digest, str) or not raw_digest:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Bundle metadata missing",
                )
            bundle_sha256 = raw_digest
    if not bundle_path_value:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bundle path missing",
        )
    bundle_path = Path(bundle_path_value)
    if not bundle_path.is_absolute():
        bundle_path = REPO_ROOT / bundle_path
    if not bundle_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bundle path missing",
        )
    manifest = _load_yaml_file(bundle_path / "manifest.yaml")
    bundle_id = bundle_id or manifest.get("bundle_id")
    runtime_compatibility = manifest.get("runtime_compatibility", {})
    min_version = runtime_compatibility.get("min_version")
    if not bundle_id or not min_version:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bundle metadata missing",
        )
    return str(bundle_id), str(min_version), bundle_sha256


def _map_error_code(exc: Exception, http_status: int) -> str:
    if http_status == status.HTTP_401_UNAUTHORIZED:
        return "unauthorized"
    if http_status == status.HTTP_403_FORBIDDEN:
        return "forbidden"
    if http_status == status.HTTP_500_INTERNAL_SERVER_ERROR:
        if isinstance(exc.__cause__, (AuthConfigError, AuditConfigError)):
            return "config_error"
        if isinstance(exc, AuthConfigError):
            return "config_error"
        if isinstance(exc, HTTPException) and "config" in str(exc.detail).lower():
            return "config_error"
    return "internal_error"


@app.get("/tenants/{tenant_id}/resolve/current")
def resolve_current(
    tenant_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
) -> dict[str, Any]:
    started_at = time.time()
    request_id = (
        x_request_id
        if isinstance(x_request_id, str) and x_request_id.strip()
        else str(uuid.uuid4())
    )
    status_code = status.HTTP_200_OK
    bundle_id: str | None = None
    error_code: str | None = None

    try:
        enforce_control_plane_auth(
            tenant_id=tenant_id, authorization=authorization, x_tenant_id=x_tenant_id
        )
        bundle_id, min_version, bundle_sha256 = resolve_current_bundle_metadata(tenant_id)
        payload = {
            "bundle_id": bundle_id,
            "runtime_compatibility": {"min_version": min_version},
        }
        if bundle_sha256:
            payload["bundle_sha256"] = bundle_sha256
        return payload
    except HTTPException as exc:
        status_code = exc.status_code
        error_code = _map_error_code(exc, status_code)
        raise
    except AuthConfigError as exc:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = "config_error"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = _map_error_code(exc, status_code)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from exc
    finally:
        event: dict[str, Any] = {
            "ts_utc": now_utc_iso(),
            "service": "control_plane",
            "event": "resolve_current",
            "tenant_id": tenant_id,
            "request_id": request_id,
            "actor": "runtime",
            "outcome": "ok" if status_code < 400 else "error",
            "http_status": int(status_code),
            "latency_ms": int((time.time() - started_at) * 1000),
        }
        if bundle_id:
            event["bundle_id"] = bundle_id
        if error_code:
            event["error_code"] = error_code
        try:
            audit_emit(event)
        except AuditConfigError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc


@app.post("/tenants/{tenant_id}/bundles/{bundle_id}/gates")
def run_quality_gate(
    tenant_id: str,
    bundle_id: str,
    gate_request: GateRunRequest,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
) -> dict[str, Any]:
    started_at = time.time()
    request_id = (
        x_request_id
        if isinstance(x_request_id, str) and x_request_id.strip()
        else str(uuid.uuid4())
    )
    gate_id = str(uuid.uuid4())
    status_code = status.HTTP_200_OK
    outcome = "pass"
    summary = {"total": 0, "passed": 0, "failed": 0}

    try:
        enforce_control_plane_auth(
            tenant_id=tenant_id, authorization=authorization, x_tenant_id=x_tenant_id
        )
        bundle_path = _find_bundle_path_by_bundle_id(bundle_id)
        suite_paths = _list_suite_paths(bundle_path, gate_request.suite_id)

        suites_result: list[dict[str, Any]] = []
        for suite_path in suite_paths:
            suite_cases = _load_and_validate_suite(suite_path)
            _ensure_suite_matches_tenant(suite_cases, tenant_id)
            case_results, passed_count, failed_count = _run_suite_cases(suite_cases, request_id)
            suite_outcome = "pass" if failed_count == 0 else "fail"
            suites_result.append(
                {
                    "suite_id": suite_path.stem,
                    "total": len(suite_cases),
                    "passed": passed_count,
                    "failed": failed_count,
                    "outcome": suite_outcome,
                    "cases": case_results,
                }
            )
            summary["total"] += len(suite_cases)
            summary["passed"] += passed_count
            summary["failed"] += failed_count

        if summary["failed"] > 0:
            outcome = "fail"

        payload = {
            "gate_id": gate_id,
            "request_id": request_id,
            "tenant_id": tenant_id,
            "bundle_id": bundle_id,
            "status": "completed",
            "outcome": outcome,
            "created_at": now_utc_iso(),
            "criteria": {"pass_rule": "all_cases_must_pass", "max_failures": 0},
            "summary": summary,
            "suites": suites_result,
        }
        _atomic_write_json(_gate_storage_file(tenant_id, bundle_id, gate_id), payload)
        return payload
    except HTTPException as exc:
        status_code = exc.status_code
        outcome = "error"
        raise
    except RuntimeConfigError as exc:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        outcome = "error"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        outcome = "error"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from exc
    finally:
        event: dict[str, Any] = {
            "ts_utc": now_utc_iso(),
            "service": "control_plane",
            "event": "quality_gate_run",
            "tenant_id": tenant_id,
            "bundle_id": bundle_id,
            "gate_id": gate_id,
            "request_id": request_id,
            "actor": "control_plane_api",
            "outcome": outcome,
            "http_status": int(status_code),
            "latency_ms": int((time.time() - started_at) * 1000),
            "summary": {
                "total": summary["total"],
                "passed": summary["passed"],
                "failed": summary["failed"],
            },
        }
        try:
            audit_emit(event)
        except AuditConfigError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc


@app.get("/tenants/{tenant_id}/bundles/{bundle_id}/gates/history")
def list_quality_gates_history(
    tenant_id: str,
    bundle_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
) -> dict[str, Any]:
    enforce_control_plane_auth(
        tenant_id=tenant_id, authorization=authorization, x_tenant_id=x_tenant_id
    )
    bundle_dir = GATE_STORAGE_ROOT / tenant_id / bundle_id
    if not bundle_dir.exists():
        return {
            "tenant_id": tenant_id,
            "bundle_id": bundle_id,
            "limit": GATE_HISTORY_LIMIT,
            "items": [],
        }

    paths = sorted(
        bundle_dir.glob("*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )[:GATE_HISTORY_LIMIT]
    items: list[dict[str, Any]] = []
    for path in paths:
        payload = _load_gate_result(tenant_id, bundle_id, path.stem)
        items.append(
            {
                "gate_id": payload.get("gate_id", path.stem),
                "request_id": payload.get("request_id"),
                "created_at": payload.get("created_at"),
                "status": payload.get("status"),
                "outcome": payload.get("outcome"),
                "summary": payload.get("summary"),
            }
        )
    return {
        "tenant_id": tenant_id,
        "bundle_id": bundle_id,
        "limit": GATE_HISTORY_LIMIT,
        "items": items,
    }


@app.get("/tenants/{tenant_id}/bundles/{bundle_id}/gates/{gate_id}")
def get_quality_gate(
    tenant_id: str,
    bundle_id: str,
    gate_id: str,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
) -> dict[str, Any]:
    enforce_control_plane_auth(
        tenant_id=tenant_id, authorization=authorization, x_tenant_id=x_tenant_id
    )
    return _load_gate_result(tenant_id, bundle_id, gate_id)
