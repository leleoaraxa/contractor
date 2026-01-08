# app/shared/security/rate_limit.py
from __future__ import annotations

import importlib
import importlib.util
import logging
import math
import os
import threading
import time
from dataclasses import dataclass
from typing import Tuple
from urllib.parse import urlsplit, urlunsplit

from fastapi import HTTPException, status

from app.shared.config.settings import settings

logger = logging.getLogger(__name__)


class RateLimitBackendUnavailableError(RuntimeError):
    def __init__(self, backend: str, message: str) -> None:
        super().__init__(message)
        self.backend = backend
        self.safe_message = message


def _redact_redis_url(url: str) -> str:
    try:
        parts = urlsplit(url)
    except Exception:
        return "<invalid-url>"
    netloc = parts.netloc
    if "@" in netloc:
        creds, host = netloc.rsplit("@", 1)
        if ":" in creds:
            user, _ = creds.split(":", 1)
            creds = f"{user}:[REDACTED]"
        else:
            creds = "[REDACTED]"
        netloc = f"{creds}@{host}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


@dataclass
class RateLimitResult:
    allowed: bool
    tokens_left: float
    retry_after_seconds: float


class _BaseRateLimitBackend:
    name = "base"

    def consume(
        self, key: str, rps: float, burst: float
    ) -> RateLimitResult:  # pragma: no cover
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
        try:
            self.client.ping()
        except Exception as exc:  # pragma: no cover - defensive
            raise RateLimitBackendUnavailableError(
                "redis", f"redis ping failed ({exc.__class__.__name__})"
            ) from exc

    def _connect(self, url: str):
        redis_spec = importlib.util.find_spec("redis")
        if not redis_spec:
            raise RateLimitBackendUnavailableError("redis", "redis client not available")
        redis_mod = importlib.import_module("redis")
        return redis_mod.from_url(url, decode_responses=True)

    def consume(self, key: str, rps: float, burst: float) -> RateLimitResult:
        try:
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
        except Exception as exc:  # pragma: no cover - defensive
            raise RateLimitBackendUnavailableError(
                "redis", f"redis error ({exc.__class__.__name__})"
            ) from exc


class _UnavailableRateLimitBackend(_BaseRateLimitBackend):
    name = "unavailable"

    def __init__(self, backend: str, reason: str) -> None:
        self.backend = backend
        self.reason = reason

    def consume(self, key: str, rps: float, burst: float) -> RateLimitResult:
        raise RateLimitBackendUnavailableError(self.backend, self.reason)


class _DisabledRateLimitBackend(_BaseRateLimitBackend):
    name = "disabled"

    def consume(self, key: str, rps: float, burst: float) -> RateLimitResult:
        return RateLimitResult(allowed=True, tokens_left=burst, retry_after_seconds=0.0)


class TokenBucketRateLimiter:
    def __init__(self) -> None:
        self.rps = max(0, settings.rate_limit_rps)
        self.burst = max(0, settings.rate_limit_burst)
        self.using_memory_fallback = False
        self.backend = self._select_backend()

    def _select_backend(self) -> _BaseRateLimitBackend:
        redis_url = settings.rate_limit_redis_url or settings.runtime_redis_url
        forced_backend = os.getenv("RATE_LIMIT_BACKEND")
        if forced_backend:
            forced_backend = forced_backend.strip().lower()
            if forced_backend == "memory":
                logger.warning(
                    "rate limiter backend forced to memory via RATE_LIMIT_BACKEND"
                )
                self.using_memory_fallback = True
                return _MemoryRateLimitBackend()
            if forced_backend == "disabled":
                logger.warning(
                    "rate limiter backend forced to disabled via RATE_LIMIT_BACKEND"
                )
                return _DisabledRateLimitBackend()
            if forced_backend == "redis":
                return self._create_redis_backend(redis_url)
            logger.warning(
                "rate limiter backend %r not recognized; using default selection",
                forced_backend,
            )

        if redis_url:
            return self._create_redis_backend(redis_url)
        logger.warning("rate limiter: Redis not configured, using in-memory backend")
        self.using_memory_fallback = True
        return _MemoryRateLimitBackend()

    def _create_redis_backend(self, redis_url: str | None) -> _BaseRateLimitBackend:
        if not redis_url:
            logger.error("rate limiter redis backend unavailable (url=missing)")
            return _UnavailableRateLimitBackend("redis", "redis url missing")
        if redis_url:
            try:
                return _RedisRateLimitBackend(redis_url)
            except RateLimitBackendUnavailableError as exc:  # pragma: no cover - defensive
                safe_url = _redact_redis_url(redis_url)
                logger.error(
                    "rate limiter redis backend unavailable (url=%s, error=%s)",
                    safe_url,
                    exc.safe_message,
                )
                return _UnavailableRateLimitBackend("redis", exc.safe_message)
            except Exception as exc:  # pragma: no cover - defensive
                safe_url = _redact_redis_url(redis_url)
                logger.error(
                    "rate limiter redis backend unavailable (url=%s, error=%s)",
                    safe_url,
                    exc.__class__.__name__,
                )
                return _UnavailableRateLimitBackend(
                    "redis", f"redis backend error ({exc.__class__.__name__})"
                )
        return _UnavailableRateLimitBackend("redis", "redis backend unavailable")

    def consume(
        self,
        tenant_id: str,
        scope: str,
        rps: float | None = None,
        burst: float | None = None,
    ) -> RateLimitResult:
        use_rps = self.rps if rps is None else max(0.0, float(rps))
        use_burst = self.burst if burst is None else max(0.0, float(burst))

        if use_rps <= 0 or use_burst <= 0:
            return RateLimitResult(
                allowed=True, tokens_left=use_burst, retry_after_seconds=0.0
            )

        key = f"rl|tenant:{tenant_id}|scope:{scope}"
        return self.backend.consume(key, use_rps, use_burst)


_RL = TokenBucketRateLimiter()


def _reset_rate_limiter_for_tests() -> None:
    global _RL
    _RL = TokenBucketRateLimiter()


def enforce_rate_limit(
    tenant_id: str,
    scope: str,
    rps: float | None = None,
    burst: float | None = None,
) -> None:
    try:
        result = _RL.consume(tenant_id=tenant_id, scope=scope, rps=rps, burst=burst)
    except RateLimitBackendUnavailableError as exc:
        logger.error(
            "rate limiter backend unavailable (backend=%s, error=%s)",
            exc.backend,
            exc.safe_message,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "rate_limit_backend_unavailable",
                "backend": exc.backend,
                "message": exc.safe_message,
            },
        ) from exc
    if not result.allowed:
        retry_after = max(1, int(math.ceil(result.retry_after_seconds)))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "rate_limit_exceeded", "retry_after_seconds": retry_after},
            headers={"Retry-After": str(retry_after)},
        )
