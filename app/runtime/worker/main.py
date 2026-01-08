# app/runtime/worker/main.py
from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict

from app.runtime.engine.ask_handler import handle_ask
from app.runtime.engine.ask_models import AskRequest
from app.runtime.worker import metrics
from app.runtime.worker import queue
from app.shared.config.settings import settings
from app.shared.logging.logger import configure_logging

logger = logging.getLogger("runtime.worker")


def _process_job(job_payload: Dict[str, Any]) -> None:
    request_id = job_payload.get("request_id")
    payload = dict(job_payload.get("payload") or {})
    ttl_s = int(job_payload.get("ttl_s") or getattr(settings, "runtime_async_result_ttl_seconds", 600))
    if not request_id:
        raise ValueError("job missing request_id")

    explain_enabled = bool(payload.pop("explain", False))
    req = AskRequest(**payload)
    result = handle_ask(req, explain_enabled)
    queue.write_result(request_id, result.model_dump(), ttl_s=ttl_s)


def run() -> None:
    configure_logging()
    if not queue.is_available():
        raise RuntimeError("Redis unavailable: runtime_redis_url must be configured")

    block_timeout = getattr(settings, "runtime_async_worker_block_seconds", 5)

    while True:
        try:
            raw = queue.get_client().blpop(queue.QUEUE_KEY, timeout=block_timeout)
        except Exception as exc:
            logger.error("worker.redis_error", extra={"error": str(exc)})
            time.sleep(1)
            continue

        if not raw:
            depth = queue.queue_depth()
            if depth is not None:
                metrics.record_queue_depth(depth)
            continue

        _, job_raw = raw
        start = metrics.start_timer()
        request_id = None
        try:
            job_payload = json.loads(job_raw)
            request_id = job_payload.get("request_id")
            _process_job(job_payload)
        except Exception as exc:
            metrics.record_processed("fail", metrics.stop_timer(start))
            logger.error("worker.job_failed", extra={"error": str(exc)})
            if request_id:
                try:
                    queue.write_result(
                        request_id,
                        {"detail": {"error": "worker_failed", "message": str(exc)}},
                        ttl_s=int(
                            job_payload.get("ttl_s")
                            or getattr(settings, "runtime_async_result_ttl_seconds", 600)
                        ),
                    )
                except Exception as write_exc:
                    logger.error("worker.result_write_failed", extra={"error": str(write_exc)})
            continue

        metrics.record_processed("ok", metrics.stop_timer(start))
        depth = queue.queue_depth()
        if depth is not None:
            metrics.record_queue_depth(depth)


if __name__ == "__main__":
    run()
