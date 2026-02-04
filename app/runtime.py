# app/runtime.py
from __future__ import annotations

import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any

import yaml
from fastapi import Depends, FastAPI, Header, HTTPException, status
from jinja2 import Environment, FileSystemLoader, select_autoescape
from jsonschema import Draft202012Validator
from pydantic import BaseModel

logger = logging.getLogger("contractor.runtime")


class ExecuteRequest(BaseModel):
    question: str


class RuntimeConfigError(RuntimeError):
    pass


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALIAS_PATH = REPO_ROOT / "data" / "control_plane" / "demo_aliases.json"
DEFAULT_TENANT_KEYS_PATH = REPO_ROOT / "data" / "runtime" / "tenants.json"


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
        return json.loads(env_value)
    file_path = Path(os.getenv("CONTRACTOR_TENANT_KEYS_PATH", DEFAULT_TENANT_KEYS_PATH))
    return _load_json_file(file_path)


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


def resolve_current_bundle(tenant_id: str) -> tuple[Path, str]:
    config = load_alias_config()
    tenants = config.get("tenants", config)
    tenant_entry = tenants.get(tenant_id) or tenants.get("*")
    if not tenant_entry:
        raise RuntimeConfigError("Tenant alias not configured")
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
    return bundle_path, bundle_id


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
    if not tenant_id or not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized"
        )
    keys = load_tenant_keys()
    expected_key = keys.get(tenant_id)
    if not expected_key or expected_key != api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return tenant_id


app = FastAPI()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/execute")
def execute(
    request: ExecuteRequest, tenant_id: str = Depends(authenticate)
) -> dict[str, Any]:
    request_id = str(uuid.uuid4())
    try:
        bundle_path, bundle_id = resolve_current_bundle(tenant_id)
    except RuntimeConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

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

    audit_event = {
        "event_type": "runtime_exec",
        "tenant_id": tenant_id,
        "bundle_id": bundle_id,
        "request_id": request_id,
        "intent": intent_name,
        "status": status_value,
    }
    logger.info("runtime_exec %s", json.dumps(audit_event, ensure_ascii=False))

    return {
        "request_id": request_id,
        "bundle_id": bundle_id,
        "tenant_id": tenant_id,
        "intent": intent_name,
        "status": status_value,
        "output_text": output_text,
        "result": payload,
    }
