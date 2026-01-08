# app/runtime/worker/queue.py
from __future__ import annotations

import importlib
import importlib.util
import json
import time
from typing import Any, Dict, Optional

from app.shared.config.settings import settings

QUEUE_KEY = "contractor:queue:ask"
RESULT_PREFIX = "contractor:result:"
PENDING_PREFIX = "contractor:pending:"


class RedisUnavailableError(RuntimeError):
    pass


class ResultNotReady(RuntimeError):
    pass


class ResultExpired(RuntimeError):
    pass


_REDIS_CLIENT = None


def _connect(url: str):
    redis_spec = importlib.util.find_spec("redis")
    if not redis_spec:
        raise RedisUnavailableError("redis client not available")
    redis_mod = importlib.import_module("redis")
    return redis_mod.from_url(url, decode_responses=True)


def _get_client():
    global _REDIS_CLIENT
    redis_url = getattr(settings, "runtime_redis_url", None)
    if not redis_url:
        raise RedisUnavailableError("runtime_redis_url not configured")
    if _REDIS_CLIENT is None:
        _REDIS_CLIENT = _connect(redis_url)
    return _REDIS_CLIENT


def get_client():
    return _get_client()


def is_available() -> bool:
    try:
        client = _get_client()
        client.ping()
    except Exception:
        return False
    return True


def _result_key(request_id: str) -> str:
    return f"{RESULT_PREFIX}{request_id}"


def _pending_key(request_id: str) -> str:
    return f"{PENDING_PREFIX}{request_id}"


def enqueue_job(request_id: str, payload: Dict[str, Any], ttl_s: int) -> None:
    client = _get_client()
    job = {
        "request_id": request_id,
        "payload": payload,
        "ttl_s": ttl_s,
        "queued_at": time.time(),
    }
    client.setex(_pending_key(request_id), ttl_s, "pending")
    client.rpush(QUEUE_KEY, json.dumps(job, ensure_ascii=False))


def read_result(request_id: str) -> Dict[str, Any]:
    client = _get_client()
    raw = client.get(_result_key(request_id))
    if raw is not None:
        return json.loads(raw)

    if client.exists(_pending_key(request_id)):
        raise ResultNotReady("result not ready")
    raise ResultExpired("result expired or not found")


def write_result(request_id: str, result_payload: Dict[str, Any], ttl_s: Optional[int] = None) -> None:
    client = _get_client()
    ttl = ttl_s or getattr(settings, "runtime_async_result_ttl_seconds", 600)
    client.setex(_result_key(request_id), ttl, json.dumps(result_payload, ensure_ascii=False))
    client.delete(_pending_key(request_id))


def queue_depth() -> Optional[int]:
    try:
        client = _get_client()
    except RedisUnavailableError:
        return None
    try:
        return int(client.llen(QUEUE_KEY))
    except Exception:
        return None
