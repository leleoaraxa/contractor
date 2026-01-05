# app/runtime/engine/cache/rt_cache.py
from __future__ import annotations

import importlib
import importlib.util
import json
import time
from collections import OrderedDict
from hashlib import sha256
from typing import Any, Dict, Optional, Tuple

from app.runtime.engine.context.tenant_context import TenantContext
from app.runtime.engine.contracts.models import CacheMeta
from app.runtime.engine.policies.policy_loader import CachePolicy
from app.shared.config.settings import settings


class _BaseBackend:
    name = "base"

    def get(self, key: str) -> Optional[Dict[str, Any]]:  # pragma: no cover - interface
        raise NotImplementedError

    def set(self, key: str, value: Dict[str, Any], ttl_seconds: Optional[int]) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class _MemoryLRUBackend(_BaseBackend):
    name = "memory"

    def __init__(self, max_entries: int = 512) -> None:
        self.max_entries = max_entries
        self.store: OrderedDict[str, Tuple[Dict[str, Any], Optional[float]]] = OrderedDict()

    def _evict(self) -> None:
        while len(self.store) > self.max_entries:
            self.store.popitem(last=False)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        now = time.time()
        item = self.store.get(key)
        if not item:
            return None

        value, expires_at = item
        if expires_at and expires_at < now:
            self.store.pop(key, None)
            return None

        # refresh LRU order
        self.store.move_to_end(key)
        return value

    def set(self, key: str, value: Dict[str, Any], ttl_seconds: Optional[int]) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        self.store[key] = (value, expires_at)
        self.store.move_to_end(key)
        self._evict()


class _RedisBackend(_BaseBackend):
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

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        raw = self.client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def set(self, key: str, value: Dict[str, Any], ttl_seconds: Optional[int]) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        if ttl_seconds:
            self.client.setex(key, ttl_seconds, payload)
        else:
            self.client.set(key, payload)


_MEMORY_BACKEND = _MemoryLRUBackend()
_REDIS_BACKEND: Optional[_RedisBackend] = None
_CACHE_METRICS: Dict[str, Any] = {
    "hits": 0,
    "misses": 0,
    "bypassed": 0,
    "errors": 0,
    "latency_ms_total": 0.0,
}


class RuntimeCache:
    """
    Runtime cache service (ADR 0008).

    * Key = tenant_id + bundle_id + canonical_request_hash
    * Backend: Redis (if available) with fallback to in-memory LRU
    * TTL: policy-driven
    * Metrics: hits/misses/latency (in-memory counters)
    """

    def __init__(self, ctx: TenantContext, policy: CachePolicy) -> None:
        self.ctx = ctx
        self.policy = policy
        self.backend = self._select_backend()

    def _select_backend(self) -> _BaseBackend:
        global _REDIS_BACKEND
        redis_url = getattr(settings, "runtime_redis_url", None)
        if redis_url:
            try:
                _REDIS_BACKEND = _REDIS_BACKEND or _RedisBackend(redis_url)
                return _REDIS_BACKEND
            except Exception:
                _CACHE_METRICS["errors"] += 1
        return _MEMORY_BACKEND

    def _canonical_hash(self, payload: Dict[str, Any]) -> str:
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return sha256(serialized.encode("utf-8")).hexdigest()

    def _build_key(self, canonical_hash: str) -> str:
        return f"tenant:{self.ctx.tenant_id}|bundle:{self.ctx.bundle_id}|{canonical_hash}"

    def _record_metrics(self, hit: Optional[bool], latency_ms: float, bypass: bool = False) -> None:
        if bypass:
            _CACHE_METRICS["bypassed"] += 1
        elif hit is True:
            _CACHE_METRICS["hits"] += 1
        elif hit is False:
            _CACHE_METRICS["misses"] += 1
        _CACHE_METRICS["latency_ms_total"] += latency_ms

    def read(self, canonical_payload: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], CacheMeta]:
        cache_meta = CacheMeta(backend=self.backend.name, ttl_seconds=self.policy.default_ttl_seconds)

        if not self.policy.enabled:
            cache_meta.bypassed = True
            self._record_metrics(hit=False, latency_ms=0.0, bypass=True)
            cache_meta.metrics = dict(_CACHE_METRICS)
            return None, cache_meta

        start = time.perf_counter()
        key = self._build_key(self._canonical_hash(canonical_payload))
        cache_meta.cache_key = key
        try:
            cached = self.backend.get(key)
        except Exception:
            cached = None
            _CACHE_METRICS["errors"] += 1
        latency_ms = (time.perf_counter() - start) * 1000
        cache_meta.latency_ms = round(latency_ms, 3)
        cache_meta.cache_hit = cached is not None
        self._record_metrics(hit=cache_meta.cache_hit, latency_ms=latency_ms)
        cache_meta.metrics = dict(_CACHE_METRICS)
        return cached, cache_meta

    def write(
        self,
        canonical_payload: Dict[str, Any],
        value: Dict[str, Any],
        cache_meta: CacheMeta,
        ttl_override: Optional[int] = None,
    ) -> CacheMeta:
        cache_meta = cache_meta.model_copy()
        if not self.policy.enabled:
            cache_meta.bypassed = True
            self._record_metrics(hit=False, latency_ms=0.0, bypass=True)
            cache_meta.metrics = dict(_CACHE_METRICS)
            return cache_meta

        ttl = self.policy.default_ttl_seconds if ttl_override is None else ttl_override
        ttl = max(0, min(ttl, self.policy.max_ttl_seconds))

        if ttl == 0:
            cache_meta.bypassed = True
            self._record_metrics(hit=False, latency_ms=0.0, bypass=True)
            cache_meta.metrics = dict(_CACHE_METRICS)
            return cache_meta

        key = cache_meta.cache_key or self._build_key(self._canonical_hash(canonical_payload))
        cache_meta.cache_key = key

        start = time.perf_counter()
        try:
            self.backend.set(key, value, ttl_seconds=ttl)
        except Exception:
            _CACHE_METRICS["errors"] += 1
            cache_meta.bypassed = True
        latency_ms = (time.perf_counter() - start) * 1000
        cache_meta.latency_ms = round(latency_ms, 3)
        cache_meta.ttl_seconds = ttl
        self._record_metrics(hit=None, latency_ms=latency_ms, bypass=cache_meta.bypassed)
        cache_meta.metrics = dict(_CACHE_METRICS)
        return cache_meta
