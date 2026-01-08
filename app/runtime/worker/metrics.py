# app/runtime/worker/metrics.py
from __future__ import annotations

import time
from typing import Dict

_ASYNC_METRICS: Dict[str, float] = {
    "runtime_async_jobs_enqueued_total": 0,
    "runtime_async_jobs_processed_total_ok": 0,
    "runtime_async_jobs_processed_total_fail": 0,
    "runtime_async_job_latency_seconds_total": 0.0,
    "runtime_async_job_latency_seconds_count": 0,
    "runtime_async_job_latency_seconds_max": 0.0,
    "runtime_async_queue_depth": 0,
}


def record_enqueue() -> None:
    _ASYNC_METRICS["runtime_async_jobs_enqueued_total"] += 1


def record_processed(outcome: str, latency_seconds: float) -> None:
    if outcome == "ok":
        _ASYNC_METRICS["runtime_async_jobs_processed_total_ok"] += 1
    else:
        _ASYNC_METRICS["runtime_async_jobs_processed_total_fail"] += 1
    _ASYNC_METRICS["runtime_async_job_latency_seconds_total"] += latency_seconds
    _ASYNC_METRICS["runtime_async_job_latency_seconds_count"] += 1
    if latency_seconds > _ASYNC_METRICS["runtime_async_job_latency_seconds_max"]:
        _ASYNC_METRICS["runtime_async_job_latency_seconds_max"] = latency_seconds


def record_queue_depth(depth: int) -> None:
    _ASYNC_METRICS["runtime_async_queue_depth"] = depth


def start_timer() -> float:
    return time.perf_counter()


def stop_timer(start: float) -> float:
    return max(0.0, time.perf_counter() - start)


def snapshot() -> Dict[str, float]:
    return dict(_ASYNC_METRICS)
