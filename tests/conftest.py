# tests/conftest.py
from __future__ import annotations

import os

import pytest

os.environ.setdefault("RATE_LIMIT_BACKEND", "memory")
os.environ.setdefault("RATE_LIMIT_RPS", "0.001")
os.environ.setdefault("RATE_LIMIT_BURST", "1")


@pytest.fixture(autouse=True)
def _reset_rate_limit_state():
    from app.shared.security import rate_limit as rl

    rl._reset_rate_limiter_for_tests()
    if hasattr(rl._RL.backend, "state"):
        rl._RL.backend.state.clear()
