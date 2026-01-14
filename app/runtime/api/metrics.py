from __future__ import annotations

from prometheus_client import Counter, Histogram

from app.runtime.engine.runtime_identity import get_runtime_identity

_RUNTIME_TENANT_HTTP_REQUESTS = Counter(
    "runtime_tenant_http_requests_total",
    "Total runtime ask requests per tenant and status code.",
    ["tenant_id", "status_code"],
)
_RUNTIME_TENANT_HTTP_LATENCY = Histogram(
    "runtime_tenant_http_request_latency_seconds",
    "Latency for runtime ask requests per tenant and status code.",
    ["tenant_id", "status_code"],
)


def record_tenant_request(tenant_id: str, status_code: int, latency_seconds: float) -> None:
    identity = get_runtime_identity()
    if not identity.dedicated_tenant_id:
        return
    if tenant_id != identity.dedicated_tenant_id:
        return
    labels = {"tenant_id": identity.dedicated_tenant_id, "status_code": str(status_code)}
    _RUNTIME_TENANT_HTTP_REQUESTS.labels(**labels).inc()
    _RUNTIME_TENANT_HTTP_LATENCY.labels(**labels).observe(latency_seconds)
