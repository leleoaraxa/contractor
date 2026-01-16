# app/control_plane/domain/quality/service.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List

from app.control_plane.domain.bundles.validator import (
    ManifestNotFoundError,
    validate_bundle,
)
from app.control_plane.domain.audit.logger import AuditLogger
from app.control_plane.domain.quality.reports import (
    PromotionSetRepository,
    QualityReportRepository,
    current_commit_hash,
)
from app.control_plane.domain.quality.runner import run_suite, runtime_request_headers
from app.control_plane.domain.templates.safety import TemplateSafetyValidator
from app.shared.config.settings import settings


def _utcnow() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _is_stub_suite(suite_result: Dict) -> bool:
    markers = {
        str(suite_result.get("suite_id") or "").strip().lower(),
        str(suite_result.get("suite_source") or "").strip().lower(),
        str(suite_result.get("suite_path") or "").strip().lower(),
    }
    return "stub" in markers


class QualityService:
    def __init__(
        self,
        report_repo: QualityReportRepository | None = None,
        promotion_repo: PromotionSetRepository | None = None,
        audit: AuditLogger | None = None,
    ) -> None:
        self.report_repo = report_repo or QualityReportRepository()
        self.promotion_repo = promotion_repo or PromotionSetRepository()
        self.audit = audit or AuditLogger()
        self.template_validator = TemplateSafetyValidator()
        if settings.runtime_base_url:
            self.runtime_base_url = settings.runtime_base_url.rstrip("/")
        else:
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
        template_safety = self.template_validator.validate_bundle(tenant_id, bundle_id)

        required_suites = self.promotion_repo.load(tenant_id)
        suite_results: List[Dict] = []
        suite_failures: List[Dict] = []
        runtime_headers = runtime_request_headers()

        for suite_path in required_suites:
            result = run_suite(
                base_url=self.runtime_base_url,
                suite_path=suite_path,
                bundle_id=bundle_id,
                headers=runtime_headers,
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

        if template_safety.get("status") != "pass":
            overall_failures.append(
                {"type": "template_safety", "errors": template_safety.get("errors", [])}
            )

        for sf in suite_failures:
            overall_failures.append({"type": "suite", **sf})

        status = "pass" if not overall_failures else "fail"
        finished_at = _utcnow()

        report = {
            "tenant_id": tenant_id,
            "bundle_id": bundle_id,
            "validate": validation,
            "template_safety": template_safety,
            "required_suites": required_suites,
            "suites": suite_results,
            "result": {"status": status, "failures": overall_failures},
            "timestamps": {"started_at": started_at, "finished_at": finished_at},
            "commit_hash": current_commit_hash(),
        }

        saved = self.report_repo.save(tenant_id, bundle_id, report)
        try:
            self.audit.log(
                "promotion_run",
                {
                    "tenant_id": tenant_id,
                    "bundle_id": bundle_id,
                    "status": status,
                    "required_suites": len(required_suites),
                    "failures": len(overall_failures),
                },
            )
        except Exception:
            # audit logging is best-effort
            pass
        return saved.content

    def ensure_gate(
        self,
        tenant_id: str,
        bundle_id: str,
        require_suites: bool,
        require_template_safety: bool = False,
    ) -> None:
        """
        Raises a ValueError if validation/suites are not satisfied.
        """
        try:
            validation = validate_bundle(tenant_id, bundle_id)
        except ManifestNotFoundError as e:
            raise ValueError(str(e)) from e

        if validation.get("status") != "pass":
            raise PromotionGateError(
                "validation",
                "validate_bundle failed",
                report_path=self.report_repo.path_for(tenant_id, bundle_id),
            )

        if not require_suites and not require_template_safety:
            return

        try:
            report = self.get_report(tenant_id, bundle_id)
        except FileNotFoundError as e:
            try:
                report = self.run_quality(tenant_id, bundle_id)
            except Exception as exc:
                raise PromotionGateError(
                    "quality_report_missing",
                    f"quality report not found for bundle {bundle_id} and automatic run failed; "
                    f"run POST /api/v1/control/tenants/{tenant_id}/bundles/{bundle_id}/quality/run. "
                    f"Underlying error: {e}; run error: {exc}"
                ) from exc

        if require_template_safety:
            template_gate = report.get("template_safety") or {}
            if template_gate.get("status") != "pass":
                raise PromotionGateError(
                    "template_safety",
                    f"template safety failed for bundle {bundle_id}: "
                    f"{template_gate.get('errors')}",
                    report_path=self.report_repo.path_for(tenant_id, bundle_id),
                )

        for suite in report.get("suites") or []:
            if _is_stub_suite(suite):
                raise PromotionGateError(
                    "suites",
                    "quality report contains stub suite results; rerun suites before promotion",
                    report_path=self.report_repo.path_for(tenant_id, bundle_id),
                )

        required_suites = self.promotion_repo.load(tenant_id)
        missing = [s for s in required_suites if s not in (report.get("required_suites") or [])]
        if missing:
            raise PromotionGateError(
                "suites",
                f"quality report missing required suites: {missing}",
                report_path=self.report_repo.path_for(tenant_id, bundle_id),
            )

        if (report.get("result") or {}).get("status") != "pass":
            raise PromotionGateError(
                "suites",
                f"quality report status is not pass for bundle {bundle_id}: "
                f"{(report.get('result') or {}).get('failures')}",
                report_path=self.report_repo.path_for(tenant_id, bundle_id),
            )

        # check that every required suite is pass
        suites = {}
        for s in report.get("suites") or []:
            suites[s.get("suite_source") or s.get("suite_path")] = s

        for required in required_suites:
            sr = suites.get(str(required))
            if not sr:
                raise PromotionGateError(
                    "suites",
                    f"quality report missing suite result for {required}",
                    report_path=self.report_repo.path_for(tenant_id, bundle_id),
                )
            if sr.get("status") != "pass":
                raise PromotionGateError(
                    "suites",
                    f"suite failed: {required}",
                    report_path=self.report_repo.path_for(tenant_id, bundle_id),
                )


class PromotionGateError(ValueError):
    def __init__(self, gate: str, detail: str, report_path: str | None = None) -> None:
        super().__init__(detail)
        self.gate = gate
        self.detail = detail
        self.report_path = report_path
