# app/control_plane.py
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException, status

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ALIAS_PATH = REPO_ROOT / "data" / "control_plane" / "demo_aliases.json"

app = FastAPI()


def _load_json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def _load_yaml_file(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_alias_config() -> dict[str, Any]:
    env_path = os.getenv("CONTRACTOR_CONTROL_PLANE_ALIAS_CONFIG_PATH")
    alias_path = Path(env_path) if env_path else DEFAULT_ALIAS_PATH
    return _load_json_file(alias_path)


def resolve_current_bundle_metadata(tenant_id: str) -> tuple[str, str]:
    config = load_alias_config()
    tenants = config.get("tenants", config)
    tenant_entry = tenants.get(tenant_id) or tenants.get("*")
    if not tenant_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    if isinstance(tenant_entry, str):
        bundle_path_value = tenant_entry
        bundle_id = None
    else:
        bundle_path_value = tenant_entry.get("current_bundle_path") or tenant_entry.get(
            "bundle_path"
        )
        bundle_id = tenant_entry.get("bundle_id")
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
    return str(bundle_id), str(min_version)


@app.get("/tenants/{tenant_id}/resolve/current")
def resolve_current(tenant_id: str) -> dict[str, Any]:
    bundle_id, min_version = resolve_current_bundle_metadata(tenant_id)
    return {
        "bundle_id": bundle_id,
        "runtime_compatibility": {"min_version": min_version},
    }
