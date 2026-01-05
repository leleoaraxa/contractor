from __future__ import annotations

import importlib
import importlib.util
import logging
import math
import threading
import time
from dataclasses import dataclass
from typing import Tuple

from fastapi import HTTPException, status

from app.shared.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    allowed: bool
    tokens_left: float
    retry_after_seconds: float


class _BaseRateLimitBackend:
    name = "base"

    def consume(self, key: str, rps: float, burst: float) -> RateLimitResult:  # pragma: no cover
        raise NotImplementedError


class _MemoryRateLimitBackend(_BaseRateLimitBackend):
    name = "memory"

    def __init__(self) -> None:
        self.state: dict[str, Tuple[float, float]] = {}
        self._lock = threading.Lock()

    def consume(self, key: str, rps: float, burst: float) -> RateLimitResult:
        now = time.time()
        with self._lock:
            tokens, last_ts = self.state.get(key, (burst, now))
            elapsed = max(0.0, now - last_ts)
            tokens = min(burst, tokens + elapsed * rps)

            allowed = tokens >= 1.0
            if allowed:
                tokens -= 1.0
            retry_after = 0.0 if allowed else max(0.0, (1.0 - tokens) / rps)

            self.state[key] = (tokens, now)
            return RateLimitResult(
                allowed=allowed, tokens_left=tokens, retry_after_seconds=retry_after
            )


class _RedisRateLimitBackend(_BaseRateLimitBackend):
    name = "redis"

    def __init__(self, url: str) -> None:
        self.url = url
        self.client = self._connect(url)

    def _connect(self, url: str):
        redis_spec = importlib.util.find_spec("redis")
        if not redis_spec:
            raise RuntimeError("redis client not available")
        redis_mod = importlib.import_module("redis")
        return redis_mod.from_url(url, decode_responses=True)

    def consume(self, key: str, rps: float, burst: float) -> RateLimitResult:
        now = time.time()
        pipe = self.client.pipeline()
        pipe.hget(key, "tokens")
        pipe.hget(key, "ts")
        tokens_raw, ts_raw = pipe.execute()

        tokens = float(tokens_raw) if tokens_raw is not None else burst
        last_ts = float(ts_raw) if ts_raw is not None else now
        elapsed = max(0.0, now - last_ts)
        tokens = min(burst, tokens + elapsed * rps)

        allowed = tokens >= 1.0
        if allowed:
            tokens -= 1.0

        retry_after = 0.0 if allowed else max(0.0, (1.0 - tokens) / rps)

        pipe = self.client.pipeline()
        pipe.hset(key, mapping={"tokens": tokens, "ts": now})
        ttl_seconds = int(max(math.ceil(burst / rps * 2), 1))
        pipe.expire(key, ttl_seconds)
        pipe.execute()

        return RateLimitResult(
            allowed=allowed, tokens_left=tokens, retry_after_seconds=retry_after
        )


class TokenBucketRateLimiter:
    def __init__(self) -> None:
        self.rps = max(0, settings.rate_limit_rps)
        self.burst = max(0, settings.rate_limit_burst)
        self.backend = self._select_backend()

    def _select_backend(self) -> _BaseRateLimitBackend:
        redis_url = settings.rate_limit_redis_url or settings.runtime_redis_url
        if redis_url:
            try:
                return _RedisRateLimitBackend(redis_url)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("rate limiter using in-memory backend (redis error: %s)", exc)
        return _MemoryRateLimitBackend()

    def consume(self, tenant_id: str, scope: str) -> RateLimitResult:
        if self.rps <= 0 or self.burst <= 0:
            return RateLimitResult(
                allowed=True, tokens_left=self.burst, retry_after_seconds=0.0
            )

        key = f"rl|tenant:{tenant_id}|scope:{scope}"
        return self.backend.consume(key, float(self.rps), float(self.burst))


_RL = TokenBucketRateLimiter()


def enforce_rate_limit(tenant_id: str, scope: str) -> None:
    result = _RL.consume(tenant_id=tenant_id, scope=scope)
    if not result.allowed:
        retry_after = max(1, int(math.ceil(result.retry_after_seconds)))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "rate_limit_exceeded", "retry_after_seconds": retry_after},
            headers={"Retry-After": str(retry_after)},
        )
