# app/runtime.py
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

import yaml
from fastapi import FastAPI, Header, HTTPException, Response, status
from jinja2 import Environment, FileSystemLoader, select_autoescape
from jsonschema import Draft202012Validator
from pydantic import BaseModel

from app.audit import AuditConfigError, audit_emit, now_utc_iso, sha256_hex

logger = logging.getLogger("contractor.runtime")
CONTROL_PLANE_TIMEOUT_SECONDS = 2.0


class ExecuteRequest(BaseModel):
    question: str


class RuntimeConfigError(RuntimeError):
    def __init__(
        self, message: str, *, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ) -> None:
        super().__init__(message)
        self.status_code = status_code


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALIAS_PATH = REPO_ROOT / "data" / "control_plane" / "demo_aliases.json"
DEFAULT_TENANT_KEYS_PATH = REPO_ROOT / "data" / "runtime" / "tenants.json"
DEFAULT_RATE_LIMIT_POLICY_PATH = (
    REPO_ROOT / "data" / "runtime" / "rate_limit_policy.yaml"
)
RATE_LIMIT_POLICY_ENV_JSON = "CONTRACTOR_RATE_LIMIT_POLICY_JSON"
RATE_LIMIT_POLICY_ENV_PATH = "CONTRACTOR_RATE_LIMIT_POLICY_PATH"
RATE_LIMIT_COUNTERS: dict[tuple[str, str, int], int] = {}


def _load_json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def _load_yaml_file(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_tenant_keys() -> dict[str, str]:
    env_value = os.getenv("CONTRACTOR_TENANT_KEYS")
    if env_value:
        try:
            config = json.loads(env_value)
        except json.JSONDecodeError as exc:
            raise RuntimeConfigError("Tenant keys config invalid") from exc
        return _validate_tenant_keys(config)

    file_path = Path(os.getenv("CONTRACTOR_TENANT_KEYS_PATH", DEFAULT_TENANT_KEYS_PATH))
    try:
        config = json.loads(file_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeConfigError("Tenant keys config missing") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeConfigError("Tenant keys config invalid") from exc

    return _validate_tenant_keys(config)


def load_rate_limit_policy() -> dict[str, Any]:
    env_json = os.getenv(RATE_LIMIT_POLICY_ENV_JSON)
    if env_json:
        try:
            return json.loads(env_json)
        except json.JSONDecodeError as exc:
            raise RuntimeConfigError("Rate limit policy invalid") from exc

    env_path = os.getenv(RATE_LIMIT_POLICY_ENV_PATH)
    policy_path = Path(env_path) if env_path else DEFAULT_RATE_LIMIT_POLICY_PATH
    try:
        return yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeConfigError("Rate limit policy missing") from exc
    except yaml.YAMLError as exc:
        raise RuntimeConfigError("Rate limit policy invalid") from exc


def _validate_policy_bucket(bucket: Any) -> dict[str, int]:
    if not isinstance(bucket, dict):
        raise RuntimeConfigError("Rate limit policy invalid")
    window_seconds = bucket.get("window_seconds")
    max_requests = bucket.get("max_requests")
    if not isinstance(window_seconds, int) or window_seconds <= 0:
        raise RuntimeConfigError("Rate limit policy invalid")
    if not isinstance(max_requests, int) or max_requests <= 0:
        raise RuntimeConfigError("Rate limit policy invalid")
    return {
        "window_seconds": window_seconds,
        "max_requests": max_requests,
    }


def validate_rate_limit_policy(policy: Any) -> dict[str, Any]:
    if not isinstance(policy, dict):
        raise RuntimeConfigError("Rate limit policy invalid")

    tenants = policy.get("tenants")
    if not isinstance(tenants, dict) or not tenants:
        raise RuntimeConfigError("Rate limit policy invalid")
    if "*" not in tenants:
        raise RuntimeConfigError("Rate limit policy invalid")

    normalized_tenants: dict[str, dict[str, dict[str, int]]] = {}
    for tenant_id, tenant_policy in tenants.items():
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise RuntimeConfigError("Rate limit policy invalid")
        if not isinstance(tenant_policy, dict):
            raise RuntimeConfigError("Rate limit policy invalid")
        normalized_tenants[tenant_id] = {
            "rate_limit": _validate_policy_bucket(
                tenant_policy.get("rate_limit", policy.get("rate_limit"))
            ),
            "quota": _validate_policy_bucket(
                tenant_policy.get("quota", policy.get("quota"))
            ),
        }

    return {
        "rate_limit": _validate_policy_bucket(policy.get("rate_limit")),
        "quota": _validate_policy_bucket(policy.get("quota")),
        "tenants": normalized_tenants,
    }


def _increment_window_counter(
    tenant_id: str, bucket_name: str, config: dict[str, int], now: int
) -> dict[str, int | bool]:
    window_seconds = config["window_seconds"]
    max_requests = config["max_requests"]
    window_start = now - (now % window_seconds)
    window_reset = window_start + window_seconds
    key = (tenant_id, bucket_name, window_start)

    # v1: GC determinístico para evitar crescimento infinito do map (process-local).
    # Mantém apenas janelas recentes: 2x a maior window_seconds do bucket atual.
    # (Sem Redis, sem heurística; limite explícito e estável.)
    gc_before = now - (window_seconds * 2)
    if RATE_LIMIT_COUNTERS:
        to_delete: list[tuple[str, str, int]] = []
        for k_tenant, k_bucket, k_window_start in RATE_LIMIT_COUNTERS.keys():
            if k_bucket == bucket_name and k_window_start < gc_before:
                to_delete.append((k_tenant, k_bucket, k_window_start))
        for k in to_delete:
            RATE_LIMIT_COUNTERS.pop(k, None)

    count = RATE_LIMIT_COUNTERS.get(key, 0) + 1
    RATE_LIMIT_COUNTERS[key] = count
    return {
        "max_requests": max_requests,
        "remaining": max(max_requests - count, 0),
        "reset": window_reset,
        "retry_after": max(window_reset - now, 1),
        "exceeded": count > max_requests,
    }


def enforce_rate_limit_and_quota(tenant_id: str) -> dict[str, str]:
    policy = validate_rate_limit_policy(load_rate_limit_policy())
    tenant_policy = policy["tenants"].get(tenant_id, policy["tenants"]["*"])
    now = int(time.time())

    rate_limit_decision = _increment_window_counter(
        tenant_id, "rate_limit", tenant_policy["rate_limit"], now
    )
    rate_limit_headers = {
        "X-RateLimit-Limit": str(rate_limit_decision["max_requests"]),
        "X-RateLimit-Remaining": str(rate_limit_decision["remaining"]),
        "X-RateLimit-Reset": str(rate_limit_decision["reset"]),
    }
    if rate_limit_decision["exceeded"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                **rate_limit_headers,
                "Retry-After": str(rate_limit_decision["retry_after"]),
            },
        )

    quota_decision = _increment_window_counter(
        tenant_id, "quota", tenant_policy["quota"], now
    )
    if quota_decision["exceeded"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Quota exceeded",
            headers={
                **rate_limit_headers,
                "Retry-After": str(quota_decision["retry_after"]),
            },
        )

    return rate_limit_headers


def _validate_tenant_keys(config: Any) -> dict[str, str]:
    if not isinstance(config, dict) or not config:
        raise RuntimeConfigError("Tenant keys config invalid")

    normalized: dict[str, str] = {}
    for tenant_id, api_key in config.items():
        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise RuntimeConfigError("Tenant keys config invalid")
        if not isinstance(api_key, str) or not api_key.strip():
            raise RuntimeConfigError("Tenant keys config invalid")

        tid = tenant_id.strip()
        key = api_key.strip()
        if tid in normalized:
            raise RuntimeConfigError("Tenant keys config invalid")
        normalized[tid] = key

    return normalized


def load_alias_config() -> dict[str, Any]:
    env_path = os.getenv("CONTRACTOR_ALIAS_CONFIG_PATH")
    alias_path = Path(env_path) if env_path else DEFAULT_ALIAS_PATH
    if alias_path.exists():
        return _load_json_file(alias_path)
    bundle_path = os.getenv("CONTRACTOR_DEMO_BUNDLE_PATH")
    bundle_id = os.getenv("CONTRACTOR_DEMO_BUNDLE_ID")
    if bundle_path:
        return {
            "tenants": {
                "*": {
                    "current_bundle_path": bundle_path,
                    "bundle_id": bundle_id,
                }
            }
        }
    return {}


def resolve_current_bundle(
    tenant_id: str, request_id: str | None = None
) -> tuple[Path, str, int | None]:
    base_url = os.getenv("CONTRACTOR_CONTROL_PLANE_BASE_URL")
    if base_url:
        bundle_id, min_version, control_plane_status = resolve_bundle_via_control_plane(
            tenant_id, base_url, request_id=request_id
        )
        ensure_runtime_compatibility(min_version)
        bundle_path = resolve_bundle_path_from_bootstrap_alias_config(bundle_id)
        return bundle_path, bundle_id, control_plane_status

    config = load_alias_config()
    tenants = config.get("tenants", config)
    tenant_entry = tenants.get(tenant_id) or tenants.get("*")
    if not tenant_entry:
        raise RuntimeConfigError("Tenant alias not configured")
    bundle_path, bundle_id = resolve_bundle_from_alias_entry(tenant_entry)
    return bundle_path, bundle_id, None


def resolve_bundle_via_control_plane(
    tenant_id: str, base_url: str, request_id: str | None = None
) -> tuple[str, str, int]:
    url = f"{base_url.rstrip('/')}/tenants/{tenant_id}/resolve/current"
    timeout_seconds = _resolve_control_plane_timeout()
    headers = {"X-Tenant-Id": tenant_id}
    token = os.getenv("CONTRACTOR_CONTROL_PLANE_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if request_id:
        headers["X-Request-Id"] = request_id

    try:
        with urllib_request.urlopen(
            urllib_request.Request(url, method="GET", headers=headers),
            timeout=timeout_seconds,
        ) as response:
            status_code = response.status
            payload = json.loads(response.read().decode("utf-8"))
    except urllib_error.HTTPError as exc:
        raise RuntimeConfigError(
            f"Control Plane error: {exc.code}",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc
    except urllib_error.URLError as exc:
        raise RuntimeConfigError(
            "Control Plane unreachable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeConfigError("Control Plane response invalid") from exc

    if not isinstance(payload, dict):
        raise RuntimeConfigError("Control Plane response invalid")
    bundle_id = payload.get("bundle_id")
    runtime_compatibility = payload.get("runtime_compatibility")
    if not bundle_id or not isinstance(bundle_id, str):
        raise RuntimeConfigError("Control Plane response missing bundle_id")
    if not isinstance(runtime_compatibility, dict):
        raise RuntimeConfigError("Control Plane response missing runtime_compatibility")
    min_version = runtime_compatibility.get("min_version")
    if not min_version or not isinstance(min_version, str):
        raise RuntimeConfigError("Control Plane response missing min_version")
    return bundle_id, min_version, int(status_code)


def _map_error_code(exc: Exception, http_status: int) -> str:
    if http_status == status.HTTP_401_UNAUTHORIZED:
        return "unauthorized"
    if http_status == status.HTTP_403_FORBIDDEN:
        return "forbidden"
    if http_status == status.HTTP_429_TOO_MANY_REQUESTS and isinstance(exc, HTTPException):
        if exc.detail == "Rate limit exceeded":
            return "rate_limit_exceeded"
        if exc.detail == "Quota exceeded":
            return "quota_exceeded"
    if http_status == status.HTTP_500_INTERNAL_SERVER_ERROR and isinstance(exc, HTTPException):
        if isinstance(exc.__cause__, (RuntimeConfigError, AuditConfigError)):
            return "config_error"
        if "config" in str(exc.detail).lower():
            return "config_error"
    return "internal_error"


def resolve_bundle_from_alias_entry(tenant_entry: Any) -> tuple[Path, str]:
    if isinstance(tenant_entry, str):
        bundle_path_value = tenant_entry
        bundle_id = None
    else:
        bundle_path_value = tenant_entry.get("current_bundle_path") or tenant_entry.get(
            "bundle_path"
        )
        bundle_id = tenant_entry.get("bundle_id")
    if not bundle_path_value:
        raise RuntimeConfigError("Bundle path missing for tenant alias")
    bundle_path = Path(bundle_path_value)
    if not bundle_path.is_absolute():
        bundle_path = REPO_ROOT / bundle_path
    if not bundle_path.exists():
        raise RuntimeConfigError("Bundle path does not exist")
    if not bundle_id:
        manifest = _load_yaml_file(bundle_path / "manifest.yaml")
        bundle_id = manifest.get("bundle_id")
    if not bundle_id:
        raise RuntimeConfigError("Bundle id missing")
    return bundle_path, str(bundle_id)


def resolve_bundle_path_from_bootstrap_alias_config(bundle_id: str) -> Path:
    config = load_alias_config()
    tenants = config.get("tenants", config)
    for tenant_entry in tenants.values():
        bundle_path, resolved_id = resolve_bundle_from_alias_entry(tenant_entry)
        if resolved_id == bundle_id:
            return bundle_path
    raise RuntimeConfigError(
        "Bundle path not found in bootstrap alias config for Control Plane bundle_id"
    )


def _resolve_control_plane_timeout() -> float:
    env_value = os.getenv("CONTRACTOR_CONTROL_PLANE_TIMEOUT_SECONDS")
    if not env_value:
        return CONTROL_PLANE_TIMEOUT_SECONDS
    try:
        timeout = float(env_value)
    except ValueError as exc:
        raise RuntimeConfigError("Control Plane timeout invalid") from exc
    if timeout <= 0:
        raise RuntimeConfigError("Control Plane timeout invalid")
    return timeout


def ensure_runtime_compatibility(min_version: str) -> None:
    from app import __version__ as runtime_version

    current = _parse_semver(runtime_version)
    minimum = _parse_semver(min_version)
    if current < minimum:
        raise RuntimeConfigError("Runtime incompatible with bundle")


def _parse_semver(value: str) -> tuple[int, int, int]:
    parts = value.split(".")
    if len(parts) != 3:
        raise RuntimeConfigError("Invalid runtime version format")
    try:
        return tuple(int(part) for part in parts)  # type: ignore[return-value]
    except ValueError as exc:
        raise RuntimeConfigError("Invalid runtime version format") from exc


def load_faq_index(bundle_path: Path) -> dict[str, str]:
    faq_data = json.loads(
        (bundle_path / "data" / "faq.json").read_text(encoding="utf-8")
    )
    return {item["question"]: item["answer"] for item in faq_data}


def load_intent_questions(bundle_path: Path, intent_name: str) -> set[str]:
    ontology = _load_yaml_file(bundle_path / "ontology" / "ontology.yaml")
    intents = ontology.get("intents", [])
    for intent in intents:
        if intent.get("name") == intent_name:
            match = intent.get("match", {})
            if match.get("type") != "exact":
                raise RuntimeConfigError("Intent match type must be exact for demo")
            return set(match.get("questions", []))
    raise RuntimeConfigError("Intent not found in ontology")


def load_response_validator(bundle_path: Path) -> Draft202012Validator:
    schema = _load_yaml_file(bundle_path / "entities" / "faq_answer.schema.yaml")
    return Draft202012Validator(schema)


def render_output(bundle_path: Path, payload: dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(bundle_path / "templates"),
        autoescape=select_autoescape(),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("faq_answer.j2")
    return template.render(**payload)


def authenticate(
    tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    api_key: str | None = Header(default=None, alias="X-Api-Key"),
) -> str:
    normalized_tenant_id = tenant_id.strip() if isinstance(tenant_id, str) else ""
    normalized_api_key = api_key.strip() if isinstance(api_key, str) else ""
    if not normalized_tenant_id or not normalized_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )

    try:
        keys = load_tenant_keys()
    except RuntimeConfigError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    expected_key = keys.get(normalized_tenant_id)
    if not expected_key or expected_key != normalized_api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return normalized_tenant_id


app = FastAPI()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/execute")
def execute(
    request: ExecuteRequest,
    response: Response,
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-Id"),
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
    x_request_id: str | None = Header(default=None, alias="X-Request-Id"),
) -> dict[str, Any]:
    started_at = time.time()
    request_id = (
        x_request_id
        if isinstance(x_request_id, str) and x_request_id.strip()
        else str(uuid.uuid4())
    )
    tenant_id = ""
    status_code = status.HTTP_200_OK
    bundle_id: str | None = None
    rate_limit_info: dict[str, int] | None = None
    control_plane_status: int | None = None
    error_code: str | None = None

    try:
        tenant_id = authenticate(tenant_id=x_tenant_id, api_key=x_api_key)

        try:
            rate_limit_headers = enforce_rate_limit_and_quota(tenant_id)
            rate_limit_info = {
                "limit": int(rate_limit_headers["X-RateLimit-Limit"]),
                "remaining": int(rate_limit_headers["X-RateLimit-Remaining"]),
                "reset": int(rate_limit_headers["X-RateLimit-Reset"]),
            }
        except RuntimeConfigError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

        for header_name, header_value in rate_limit_headers.items():
            response.headers[header_name] = header_value

        bundle_path, bundle_id, control_plane_status = resolve_current_bundle(
            tenant_id, request_id=request_id
        )

        intent_name = "faq_query"
        intent_questions = load_intent_questions(bundle_path, intent_name)
        answer_map = load_faq_index(bundle_path)

        status_value = "ok" if request.question in intent_questions else "no_match"
        answer = answer_map.get(request.question, "")

        payload = {
            "answer": answer,
            "intent": intent_name,
            "status": status_value,
        }

        validator = load_response_validator(bundle_path)
        errors = sorted(validator.iter_errors(payload), key=lambda err: err.path)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid response payload",
            )

        output_text = render_output(bundle_path, payload)

        return {
            "request_id": request_id,
            "bundle_id": bundle_id,
            "tenant_id": tenant_id,
            "intent": intent_name,
            "status": status_value,
            "output_text": output_text,
            "result": payload,
        }
    except HTTPException as exc:
        status_code = exc.status_code
        error_code = _map_error_code(exc, exc.status_code)
        raise
    except RuntimeConfigError as exc:
        status_code = exc.status_code
        error_code = "config_error" if "config" in str(exc).lower() else "internal_error"
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        error_code = _map_error_code(exc, status_code)
        raise HTTPException(status_code=status_code, detail="Internal server error") from exc
    finally:
        latency_ms = int((time.time() - started_at) * 1000)
        event: dict[str, Any] = {
            "ts_utc": now_utc_iso(),
            "service": "runtime",
            "event": "execute",
            "tenant_id": tenant_id,
            "request_id": request_id,
            "actor": "external_client",
            "outcome": "ok" if status_code < 400 else "error",
            "http_status": int(status_code),
            "latency_ms": latency_ms,
            "question_len": len(request.question),
            "question_sha256": sha256_hex(request.question),
        }
        if bundle_id:
            event["bundle_id"] = bundle_id
        if control_plane_status is not None:
            event["control_plane_status"] = control_plane_status
        if rate_limit_info is not None:
            event["rate_limit"] = rate_limit_info
        if error_code is not None:
            event["error_code"] = error_code
        if error_code == "config_error":
            event["error_detail"] = "config"

        try:
            audit_emit(event)
        except AuditConfigError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc
