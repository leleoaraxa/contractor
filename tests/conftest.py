# tests/conftest.py
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("RATE_LIMIT_BACKEND", "memory")
os.environ.setdefault("RATE_LIMIT_RPS", "1000")
os.environ.setdefault("RATE_LIMIT_BURST", "1000")


@pytest.fixture(autouse=True)
def _reset_rate_limit_state():
    from app.shared.security import rate_limit as rl

    rl._reset_rate_limiter_for_tests()
    if hasattr(rl._RL.backend, "state"):
        rl._RL.backend.state.clear()


@pytest.fixture(autouse=True)
def _apply_test_api_keys(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    test_api_keys = getattr(request.module, "TEST_API_KEYS", None)
    test_api_key = getattr(request.module, "TEST_API_KEY", None)

    if test_api_keys:
        monkeypatch.setenv("CONTRACTOR_API_KEYS", test_api_keys)
        monkeypatch.delenv("CONTRACTOR_API_KEY", raising=False)
    elif test_api_key:
        monkeypatch.setenv("CONTRACTOR_API_KEYS", test_api_key)
        monkeypatch.delenv("CONTRACTOR_API_KEY", raising=False)

    if test_api_keys or test_api_key:
        import importlib

        if "app.shared.config.settings" in sys.modules:
            importlib.reload(sys.modules["app.shared.config.settings"])


@pytest.fixture(autouse=True)
def _reset_runtime_cache_state() -> None:
    from app.runtime.engine.cache import rt_cache

    rt_cache._MEMORY_BACKEND.store.clear()
    rt_cache._CACHE_METRICS.update(
        {"hits": 0, "misses": 0, "bypassed": 0, "errors": 0, "latency_ms_total": 0.0}
    )
