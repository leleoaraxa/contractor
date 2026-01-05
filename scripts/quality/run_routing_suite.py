#!/usr/bin/env python3
# scripts/quality/run_routing_suite.py
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.control_plane.domain.quality.runner import run_suite


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--suite", default="data/quality/suites/demo_routing_suite.json")
    args = ap.parse_args()

    result = run_suite(base_url=args.base_url, suite_path=args.suite)
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
