# app/runtime/api/routers/ask.py
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.runtime.engine.ask_handler import execute_prepared_ask, prepare_ask
from app.runtime.engine.ask_models import AskRequest, AskResponse
from app.runtime.worker import metrics as async_metrics
from app.runtime.worker import queue as async_queue
from app.shared.config.settings import settings
from app.shared.security.auth import require_api_key

router = APIRouter()


def _is_truthy(value: str | None) -> bool:
    if not value:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _should_run_async(req: AskRequest, request: Request) -> bool:
    if _is_truthy(request.headers.get("X-Async")):
        return True
    if getattr(settings, "runtime_async_always", False):
        return True
    if getattr(settings, "runtime_async_enabled", False):
        threshold = getattr(settings, "runtime_async_question_length_threshold", 0)
        return len(req.question) > threshold
    return False


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, request: Request) -> AskResponse:
    x_explain = (request.headers.get("X-Explain") or "").strip().lower()
    explain_enabled = x_explain in {"1", "true", "yes", "y", "on"}
    require_api_key(request)

    cached_response, prep = prepare_ask(req, explain_enabled)
    if cached_response:
        return cached_response

    if _should_run_async(req, request):
        request_id = str(uuid.uuid4())
        ttl_s = getattr(settings, "runtime_async_result_ttl_seconds", 600)
        try:
            if not async_queue.is_available():
                raise async_queue.RedisUnavailableError("redis not configured or unavailable")
            job_payload = req.model_dump()
            job_payload["explain"] = explain_enabled
            async_queue.enqueue_job(request_id, job_payload, ttl_s)
        except async_queue.RedisUnavailableError as exc:
            raise HTTPException(
                status_code=503,
                detail={"error": "async_unavailable", "detail": str(exc)},
            )
        async_metrics.record_enqueue()
        depth = async_queue.queue_depth()
        if depth is not None:
            async_metrics.record_queue_depth(depth)
        return JSONResponse(
            status_code=202,
            content={"status": {"reason": "accepted"}, "request_id": request_id},
        )

    return execute_prepared_ask(prep)


@router.get("/ask/result/{request_id}")
def ask_result(request_id: str, request: Request):
    require_api_key(request)
    try:
        payload = async_queue.read_result(request_id)
    except async_queue.ResultNotReady:
        raise HTTPException(status_code=404, detail={"error": "not_ready"})
    except async_queue.ResultExpired:
        raise HTTPException(status_code=404, detail={"error": "expired"})
    except async_queue.RedisUnavailableError as exc:
        raise HTTPException(status_code=503, detail={"error": "async_unavailable", "detail": str(exc)})
    return payload
