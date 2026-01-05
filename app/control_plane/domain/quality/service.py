# app/control_plane/domain/quality/service.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from app.control_plane.domain.bundles.validator import (
    ManifestNotFoundError,
    validate_bundle,
)
from app.control_plane.domain.quality.reports import (
    PromotionSetRepository,
    QualityReportRepository,
    current_commit_hash,
)
from app.control_plane.domain.quality.runner import run_suite
from app.shared.config.settings import settings


def _utcnow() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


class QualityService:
    def __init__(
        self,
        report_repo: QualityReportRepository | None = None,
        promotion_repo: PromotionSetRepository | None = None,
    ) -> None:
        self.report_repo = report_repo or QualityReportRepository()
        self.promotion_repo = promotion_repo or PromotionSetRepository()
        host = settings.runtime_host or "localhost"
        if host == "0.0.0.0":
            host = "localhost"
        self.runtime_base_url = f"http://{host}:{settings.runtime_port}"

    def get_report(self, tenant_id: str, bundle_id: str) -> Dict:
        qr = self.report_repo.get(tenant_id, bundle_id)
        return qr.content

    def run_quality(self, tenant_id: str, bundle_id: str) -> Dict:
        started_at = _utcnow()
        validation = validate_bundle(tenant_id, bundle_id)

        required_suites = self.promotion_repo.load(tenant_id)
        suite_results: List[Dict] = []
        suite_failures: List[Dict] = []

        for suite_path in required_suites:
            result = run_suite(
                base_url=self.runtime_base_url, suite_path=suite_path, bundle_id=bundle_id
            )
            suite_results.append(result)
            if result.get("status") != "pass":
                suite_failures.append(
                    {
                        "suite_id": result.get("suite_id"),
                        "failures": result.get("failures", []),
                        "suite_path": result.get("suite_path"),
                    }
                )

        overall_failures: List[Dict] = []
        if validation.get("status") != "pass":
            overall_failures.append({"type": "validation", "errors": validation.get("errors", [])})

        for sf in suite_failures:
            overall_failures.append({"type": "suite", **sf})

        status = "pass" if not overall_failures else "fail"
        finished_at = _utcnow()

        report = {
            "tenant_id": tenant_id,
            "bundle_id": bundle_id,
            "validate": validation,
            "required_suites": required_suites,
            "suites": suite_results,
            "result": {"status": status, "failures": overall_failures},
            "timestamps": {"started_at": started_at, "finished_at": finished_at},
            "commit_hash": current_commit_hash(),
        }

        saved = self.report_repo.save(tenant_id, bundle_id, report)
        return saved.content

    def ensure_gate(self, tenant_id: str, bundle_id: str, require_suites: bool) -> None:
        """
        Raises a ValueError if validation/suites are not satisfied.
        """
        try:
            validation = validate_bundle(tenant_id, bundle_id)
        except ManifestNotFoundError as e:
            raise ValueError(str(e)) from e

        if validation.get("status") != "pass":
            raise ValueError("validate_bundle failed")

        if not require_suites:
            return

        try:
            report = self.get_report(tenant_id, bundle_id)
        except FileNotFoundError as e:
            raise ValueError(f"quality report not found: {e}") from e

        required_suites = self.promotion_repo.load(tenant_id)
        missing = [s for s in required_suites if s not in (report.get("required_suites") or [])]
        if missing:
            raise ValueError(f"quality report missing required suites: {missing}")

        if (report.get("result") or {}).get("status") != "pass":
            raise ValueError("quality report status is not pass")

        # check that every required suite is pass
        suites = {}
        for s in report.get("suites") or []:
            suites[s.get("suite_source") or s.get("suite_path")] = s

        for required in required_suites:
            sr = suites.get(str(required))
            if not sr:
                raise ValueError(f"quality report missing suite result for {required}")
            if sr.get("status") != "pass":
                raise ValueError(f"suite failed: {required}")
