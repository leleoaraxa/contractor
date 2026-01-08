# app/runtime/worker/metrics.py
from __future__ import annotations

import time

from prometheus_client import Counter, Gauge, Histogram

_ASYNC_JOBS_ENQUEUED = Counter(
    "runtime_async_jobs_enqueued_total",
    "Total number of async jobs enqueued.",
)
_ASYNC_JOBS_PROCESSED = Counter(
    "runtime_async_jobs_processed_total",
    "Total number of async jobs processed.",
    ["outcome"],
)
_ASYNC_JOB_LATENCY = Histogram(
    "runtime_async_job_latency_seconds",
    "Latency for async job processing.",
)
_ASYNC_QUEUE_DEPTH = Gauge(
    "runtime_async_queue_depth",
    "Current async queue depth.",
)


def record_enqueue() -> None:
    _ASYNC_JOBS_ENQUEUED.inc()


def record_processed(outcome: str, latency_seconds: float) -> None:
    label = "ok" if outcome == "ok" else "fail"
    _ASYNC_JOBS_PROCESSED.labels(outcome=label).inc()
    _ASYNC_JOB_LATENCY.observe(latency_seconds)


def record_queue_depth(depth: int) -> None:
    _ASYNC_QUEUE_DEPTH.set(depth)


def start_timer() -> float:
    return time.perf_counter()


def stop_timer(start: float) -> float:
    return max(0.0, time.perf_counter() - start)
