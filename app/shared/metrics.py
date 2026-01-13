from __future__ import annotations

from fastapi import FastAPI, Request
from prometheus_client import Counter

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests by service, method, path, and status code.",
    ["service", "method", "path", "status_code"],
)


def instrument_http(app: FastAPI, service: str) -> None:
    @app.middleware("http")
    async def _http_metrics_middleware(request: Request, call_next):
        response = await call_next(request)
        HTTP_REQUESTS_TOTAL.labels(
            service=service,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        ).inc()
        return response
