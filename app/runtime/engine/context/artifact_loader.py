# app/runtime/engine/context/artifact_loader.py
from __future__ import annotations

from pathlib import Path
import os
from typing import Any, Dict

import yaml

from app.shared.config.settings import settings


class ArtifactLoaderError(RuntimeError):
    pass


class ArtifactLoader:
    """
    Stage 0: filesystem-backed registry loader.
    Later (ADR 0004): S3 + metadata DB.
    """

    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.bundle_registry_base)

    def load_manifest(self, tenant_id: str, bundle_id: str) -> Dict[str, Any]:
        bundle_dir = self.base_dir / tenant_id / "bundles" / bundle_id
        manifest_path = bundle_dir / "manifest.yaml"
        if not manifest_path.exists():
            cwd = Path(os.getcwd()).resolve()
            raise ArtifactLoaderError(
                "manifest not found: "
                f"path={manifest_path} abs={manifest_path.resolve()} "
                f"base_dir={self.base_dir.resolve()} cwd={cwd}"
            )

        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        if data.get("tenant_id") not in (tenant_id, None):
            raise ArtifactLoaderError("manifest tenant_id mismatch")

        if str(data.get("bundle_id")) != str(bundle_id):
            raise ArtifactLoaderError("manifest bundle_id mismatch")

        data["_bundle_dir"] = str(bundle_dir)
        return data
