# app/control_plane/domain/quality/reports.py
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import yaml

from app.shared.config.settings import settings

_DEFAULT_PROMOTION_SUITES = [
    "data/quality/suites/demo_routing_candidate_suite.json",
    "data/quality/suites/demo_thresholds_suite.json",
]


@dataclass(frozen=True)
class QualityReport:
    tenant_id: str
    bundle_id: str
    content: Dict


class QualityReportRepository:
    def __init__(self, base_path: str | None = None) -> None:
        self.base_path = Path(base_path or settings.control_quality_report_base)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _path(self, tenant_id: str, bundle_id: str) -> Path:
        return self.base_path / tenant_id / f"{bundle_id}.json"

    def path_for(self, tenant_id: str, bundle_id: str) -> str:
        return str(self._path(tenant_id, bundle_id))

    def get(self, tenant_id: str, bundle_id: str) -> QualityReport:
        path = self._path(tenant_id, bundle_id)
        if not path.exists():
            raise FileNotFoundError(str(path))
        content = json.loads(path.read_text(encoding="utf-8"))
        return QualityReport(tenant_id=tenant_id, bundle_id=bundle_id, content=content)

    def save(self, tenant_id: str, bundle_id: str, report: Dict) -> QualityReport:
        path = self._path(tenant_id, bundle_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return QualityReport(tenant_id=tenant_id, bundle_id=bundle_id, content=report)


class PromotionSetRepository:
    def __init__(self, base_path: str | None = None) -> None:
        self.base_path = Path(base_path or settings.control_promotion_set_base)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _path(self, tenant_id: str) -> Path:
        return self.base_path / f"{tenant_id}.yaml"

    def load(self, tenant_id: str) -> List[str]:
        """
        Returns a list of suite paths that compose the promotion gate for a tenant.
        Falls back to defaults when the tenant file is missing or malformed.
        """
        path = self._path(tenant_id)
        if not path.exists():
            return list(_DEFAULT_PROMOTION_SUITES)

        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            suites = doc.get("suites") or []
            parsed = [s for s in suites if isinstance(s, str) and s.strip()]
            return parsed or list(_DEFAULT_PROMOTION_SUITES)
        except Exception:
            return list(_DEFAULT_PROMOTION_SUITES)

    def default_suites(self) -> List[str]:
        return list(_DEFAULT_PROMOTION_SUITES)


def current_commit_hash() -> str | None:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
        return out.decode("utf-8").strip()
    except Exception:
        return None
