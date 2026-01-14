# app/runtime/engine/data_residency.py
from __future__ import annotations

from app.shared.config.settings import settings

RESIDENCY_APPLIES_TO = [
    "platform_metadata",
    "operational_telemetry",
]
RESIDENCY_NOT_APPLICABLE_TO = [
    "transient_execution_data",
    "customer_domain_data",
]
EXPLICIT_NON_GUARANTEES = [
    "no_in_memory_residency_guarantee",
    "no_zero_cross_region_network_guarantee",
]
DATA_CLASSES = {
    "A": "platform_metadata",
    "B": "operational_telemetry",
    "C": "transient_execution_data",
    "D": "customer_domain_data",
}


def get_runtime_region() -> str | None:
    raw_region = getattr(settings, "runtime_region", None)
    if raw_region is None:
        return None
    normalized = str(raw_region).strip()
    return normalized or None


def get_tenant_required_region(tenant_id: str) -> str | None:
    mapping = getattr(settings, "runtime_tenant_residency_requirements", None) or {}
    required = mapping.get(tenant_id)
    if required is None:
        return None
    normalized = str(required).strip()
    return normalized or None


def get_residency_contract() -> dict:
    return {
        "runtime_region": get_runtime_region(),
        "residency_applies_to": list(RESIDENCY_APPLIES_TO),
        "residency_not_applicable_to": list(RESIDENCY_NOT_APPLICABLE_TO),
        "explicit_non_guarantees": list(EXPLICIT_NON_GUARANTEES),
        "data_classes": dict(DATA_CLASSES),
    }


def apply_residency_contract(meta: dict) -> None:
    if not meta.get("data_residency"):
        meta["data_residency"] = get_residency_contract()
