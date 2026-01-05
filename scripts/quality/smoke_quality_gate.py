#!/usr/bin/env python3
# scripts/quality/smoke_quality_gate.py
from __future__ import annotations

import argparse
import json
import sys
import os
from urllib import error, request


TRUTHY = {"1", "true", "yes", "y", "on"}
DEFAULT_API_KEY = "dev-key"


def first_non_empty_token(raw: str | None) -> str:
    if not raw:
        return ""
    for part in raw.split(","):
        token = part.strip()
        if token:
            return token
    return ""


def build_headers() -> dict[str, str]:
    auth_disabled = (os.getenv("CONTRACTOR_AUTH_DISABLED") or "").strip().lower() in TRUTHY
    if auth_disabled:
        return {}
    api_key = first_non_empty_token(os.getenv("CONTRACTOR_API_KEY"))
    if not api_key:
        api_key = first_non_empty_token(os.getenv("CONTRACTOR_API_KEYS"))
    if not api_key:
        api_key = DEFAULT_API_KEY
    return {"X-API-Key": api_key}


def get_json(url: str, headers: dict[str, str] | None = None) -> dict:
    req = request.Request(url, method="GET", headers=headers or {})
    try:
        with request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except error.HTTPError as e:
        detail = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code} GET {url}: {detail}") from e
    except Exception as e:
        raise RuntimeError(f"GET {url} failed: {e}") from e


def post_json(url: str, payload: dict, headers: dict[str, str] | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", **(headers or {})},
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
    headers = build_headers()
    aliases = get_json(f"{base}/api/v1/control/tenants/{args.tenant_id}/aliases", headers=headers)
    target_bundle = args.bundle_id or aliases.get("candidate")
    if not target_bundle:
        raise RuntimeError("target bundle_id not provided and candidate alias not set")

    print(f"[+] Run quality report for tenant={args.tenant_id} bundle={target_bundle}")
    report = post_json(
        f"{base}/api/v1/control/tenants/{args.tenant_id}/bundles/{target_bundle}/quality/run",
        {},
        headers=headers,
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
            headers=headers,
        )

        print("[+] Promote candidate -> current (gate enforced)...")
        post_json(
            f"{base}/api/v1/control/tenants/{args.tenant_id}/aliases/current",
            {"bundle_id": target_bundle},
            headers=headers,
        )
        print("[✓] Promotion succeeded.")
    finally:
        if prev_current:
            print("[+] Rollback current to previous value...")
            post_json(
                f"{base}/api/v1/control/tenants/{args.tenant_id}/aliases/current",
                {"bundle_id": prev_current},
                headers=headers,
            )
        if prev_candidate and prev_candidate != target_bundle:
            print("[+] Restore candidate to previous value...")
            post_json(
                f"{base}/api/v1/control/tenants/{args.tenant_id}/aliases/candidate",
                {"bundle_id": prev_candidate},
                headers=headers,
            )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - smoke helper
        sys.stderr.write(f"error: {exc}\n")
        raise SystemExit(1)
