#!/usr/bin/env python3
# scripts/quality/run_routing_suite.py
from __future__ import annotations

import argparse
import json
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def build_headers() -> dict[str, str]:
    truthy = {"1", "true", "yes", "y", "on"}
    auth_disabled = (os.getenv("CONTRACTOR_AUTH_DISABLED") or "").strip().lower() in truthy
    if auth_disabled:
        return {}

    def first_non_empty(raw: str | None) -> str:
        if not raw:
            return ""
        for part in raw.split(","):
            token = part.strip()
            if token:
                return token
        return ""

    DEFAULT_API_KEY = "dev-key"
    api_key = first_non_empty(os.getenv("CONTRACTOR_API_KEY"))
    if not api_key:
        api_key = first_non_empty(os.getenv("CONTRACTOR_API_KEYS"))
    if not api_key:
        api_key = DEFAULT_API_KEY
    return {"X-API-Key": api_key}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--suite", default="data/quality/suites/demo_routing_suite.json")
    args = ap.parse_args()

    try:
        from app.control_plane.domain.quality.runner import run_suite
    except ModuleNotFoundError as exc:
        missing = exc.name or ""
        if missing == "pydantic":
            raise RuntimeError(
                "Missing dependency 'pydantic'; install project deps (e.g., `pip install -e .`)"
            ) from exc
        raise

    headers = build_headers()
    result = run_suite(base_url=args.base_url, suite_path=args.suite, headers=headers)
    report = {
        "suite_id": result.get("suite_id"),
        "passed": result.get("passed"),
        "total": result.get("total"),
        "failures": result.get("failures"),
        "status": result.get("status"),
        "release_alias": result.get("release_alias"),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
