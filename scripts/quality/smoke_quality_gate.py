#!/usr/bin/env python3
# scripts/quality/smoke_quality_gate.py
from __future__ import annotations

import argparse
import json
import sys
from urllib import error, request


def get_json(url: str) -> dict:
    req = request.Request(url, method="GET")
    try:
        with request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except error.HTTPError as e:
        detail = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code} GET {url}: {detail}") from e
    except Exception as e:
        raise RuntimeError(f"GET {url} failed: {e}") from e


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/json"}
    )
    try:
        with request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except error.HTTPError as e:
        detail = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code} POST {url}: {detail}") from e
    except Exception as e:
        raise RuntimeError(f"POST {url} failed: {e}") from e


def main() -> int:
    ap = argparse.ArgumentParser(description="Smoke test for quality gate flow.")
    ap.add_argument("--tenant-id", default="demo")
    ap.add_argument("--bundle-id", help="Target bundle_id. Defaults to current candidate alias.")
    ap.add_argument("--control-base", default="http://localhost:8001")
    args = ap.parse_args()

    base = args.control_base.rstrip("/")
    aliases = get_json(f"{base}/api/v1/control/tenants/{args.tenant_id}/aliases")
    target_bundle = args.bundle_id or aliases.get("candidate")
    if not target_bundle:
        raise RuntimeError("target bundle_id not provided and candidate alias not set")

    print(f"[+] Run quality report for tenant={args.tenant_id} bundle={target_bundle}")
    report = post_json(
        f"{base}/api/v1/control/tenants/{args.tenant_id}/bundles/{target_bundle}/quality/run",
        {},
    )
    result_status = (report.get("result") or {}).get("status")
    if result_status != "pass":
        raise RuntimeError(f"quality gate failed: {(report.get('result') or {}).get('failures')}")
    print(f"[+] Quality status={result_status} suites={report.get('required_suites')}")

    prev_candidate = aliases.get("candidate")
    prev_current = aliases.get("current")

    try:
        print("[+] Set candidate alias (gate enforced)...")
        post_json(
            f"{base}/api/v1/control/tenants/{args.tenant_id}/aliases/candidate",
            {"bundle_id": target_bundle},
        )

        print("[+] Promote candidate -> current (gate enforced)...")
        post_json(
            f"{base}/api/v1/control/tenants/{args.tenant_id}/aliases/current",
            {"bundle_id": target_bundle},
        )
        print("[✓] Promotion succeeded.")
    finally:
        if prev_current:
            print("[+] Rollback current to previous value...")
            post_json(
                f"{base}/api/v1/control/tenants/{args.tenant_id}/aliases/current",
                {"bundle_id": prev_current},
            )
        if prev_candidate and prev_candidate != target_bundle:
            print("[+] Restore candidate to previous value...")
            post_json(
                f"{base}/api/v1/control/tenants/{args.tenant_id}/aliases/candidate",
                {"bundle_id": prev_candidate},
            )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - smoke helper
        sys.stderr.write(f"error: {exc}\n")
        raise SystemExit(1)
