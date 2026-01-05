# app/control_plane/api/routers/bundles.py
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
import yaml

from app.shared.config.settings import settings
from app.shared.utils.ids import validate_tenant_id
from app.control_plane.domain.bundles.contracts_validator import (
    validate_bundle_contracts,
)

router = APIRouter()

_REQUIRED_KEYS = {"bundle_id", "tenant_id", "created_at", "source", "checksum", "paths"}
_REQUIRED_PATH_KEYS = {
    "ontology_dir",
    "entities_dir",
    "policies_dir",
    "templates_dir",
    "suites_dir",
}


def _bundle_dir(tenant_id: str, bundle_id: str) -> Path:
    return Path(settings.bundle_registry_base) / tenant_id / "bundles" / bundle_id


@router.get("/tenants/{tenant_id}/bundles/{bundle_id}/validate")
def validate_bundle(tenant_id: str, bundle_id: str) -> dict:
    validate_tenant_id(tenant_id)

    bdir = _bundle_dir(tenant_id, bundle_id)
    manifest_path = bdir / "manifest.yaml"
    errors: list[dict] = []

    if not manifest_path.exists():
        raise HTTPException(
            status_code=404, detail=f"manifest not found: {manifest_path}"
        )

    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}

    missing = sorted(list(_REQUIRED_KEYS - set(data.keys())))
    if missing:
        errors.append(
            {
                "code": "manifest.missing_keys",
                "message": f"manifest missing keys: {missing}",
                "path": str(manifest_path),
            }
        )

    if str(data.get("tenant_id")) != str(tenant_id):
        errors.append(
            {
                "code": "manifest.tenant_id_mismatch",
                "message": "manifest tenant_id mismatch",
                "path": str(manifest_path),
            }
        )

    if str(data.get("bundle_id")) != str(bundle_id):
        errors.append(
            {
                "code": "manifest.bundle_id_mismatch",
                "message": "manifest bundle_id mismatch",
                "path": str(manifest_path),
            }
        )

    paths = data.get("paths") or {}
    missing_paths = sorted(list(_REQUIRED_PATH_KEYS - set(paths.keys())))
    if missing_paths:
        errors.append(
            {
                "code": "manifest.paths.missing_keys",
                "message": f"manifest.paths missing keys: {missing_paths}",
                "path": str(manifest_path),
            }
        )

    # Check declared dirs exist
    for k in sorted(_REQUIRED_PATH_KEYS):
        d = paths.get(k)
        if isinstance(d, str) and d.strip():
            p = bdir / d
            if not p.exists() or not p.is_dir():
                errors.append(
                    {
                        "code": "bundle.missing_dir",
                        "message": f"missing dir for {k}: {p}",
                        "path": str(p),
                    }
                )

    # Contract validation (ontology + policies)
    ontology_dir = str(paths.get("ontology_dir") or "ontology")
    policies_dir = str(paths.get("policies_dir") or "policies")

    contract_errs = validate_bundle_contracts(
        bundle_dir=bdir,
        ontology_dir=ontology_dir,
        policies_dir=policies_dir,
    )
    for ce in contract_errs:
        errors.append({"code": ce.code, "message": ce.message, "path": ce.path})

    status = "pass" if not errors else "fail"
    return {
        "status": status,
        "tenant_id": tenant_id,
        "bundle_id": bundle_id,
        "base_dir": str(Path(settings.bundle_registry_base).resolve()),
        "bundle_dir": str(bdir.resolve()),
        "errors": errors,
    }
