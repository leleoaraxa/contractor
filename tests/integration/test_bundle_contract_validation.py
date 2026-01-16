from __future__ import annotations

from pathlib import Path

import yaml

from app.control_plane.domain.bundles.validator import validate_bundle
import app.control_plane.domain.bundles.validator as validator_module
import app.shared.config.settings as settings_module


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def test_runtime_policy_invalid_rate_limit(tmp_path, monkeypatch) -> None:
    tenant_id = "tenant-test"
    bundle_id = "bundle-test"

    bundle_dir = tmp_path / tenant_id / "bundles" / bundle_id
    ontology_dir = bundle_dir / "ontology"
    entities_dir = bundle_dir / "entities"
    policies_dir = bundle_dir / "policies"
    templates_dir = bundle_dir / "templates"
    suites_dir = bundle_dir / "suites"

    for d in (ontology_dir, entities_dir, policies_dir, templates_dir, suites_dir):
        d.mkdir(parents=True, exist_ok=True)

    _write_yaml(
        bundle_dir / "manifest.yaml",
        {
            "bundle_id": bundle_id,
            "tenant_id": tenant_id,
            "created_at": "2026-01-05T00:01:00Z",
            "source": "test",
            "checksum": "test",
            "paths": {
                "ontology_dir": "ontology",
                "entities_dir": "entities",
                "policies_dir": "policies",
                "templates_dir": "templates",
                "suites_dir": "suites",
            },
        },
    )

    _write_yaml(
        ontology_dir / "intents.yaml",
        {"version": 1, "intents": [{"id": "status", "title": "Status"}]},
    )
    _write_yaml(
        ontology_dir / "entities.yaml",
        {"version": 1, "entities": [{"id": "platform", "title": "Platform"}]},
    )
    _write_yaml(
        ontology_dir / "terms.yaml",
        {
            "version": 1,
            "terms": [
                {
                    "term": "status",
                    "intents": ["status"],
                    "entities": ["platform"],
                }
            ],
        },
    )
    _write_yaml(
        policies_dir / "runtime.yaml",
        {"rate_limit": {"enabled": True, "rps": "fast", "burst": 1}},
    )

    monkeypatch.setattr(
        settings_module.settings, "bundle_registry_base", str(tmp_path), raising=False
    )
    monkeypatch.setattr(
        validator_module.settings, "bundle_registry_base", str(tmp_path), raising=False
    )

    result = validate_bundle(tenant_id, bundle_id)
    assert result["status"] == "fail"
    codes = {error["code"] for error in result["errors"]}
    assert "rate_limit.rps" in codes
