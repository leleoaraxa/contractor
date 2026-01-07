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


def _truncate_body(body: str, limit: int = 1024) -> str:
    if len(body) <= limit:
        return body
    return f"{body[:limit]}...[truncated]"


def _log_verbose(enabled: bool, message: str) -> None:
    if enabled:
        print(f"[verbose] {message}")


def request_json(
    method: str,
    url: str,
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
    *,
    verbose: bool = False,
    timeout: int = 10,
) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req_headers = headers or {}
    if payload is not None:
        req_headers = {"Content-Type": "application/json", **req_headers}
    req = request.Request(url, data=data, method=method, headers=req_headers)
    _log_verbose(verbose, f"{method} {url}")
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            _log_verbose(verbose, f"{method} {url} -> {resp.status}")
            return json.loads(body) if body else {}
    except error.HTTPError as e:
        detail = e.read().decode("utf-8")
        detail = _truncate_body(detail)
        _log_verbose(verbose, f"{method} {url} -> {e.code} {detail}")
        raise RuntimeError(f"HTTP {e.code} {method} {url}: {detail}") from e
    except Exception as e:
        raise RuntimeError(f"{method} {url} failed: {e}") from e


def get_json(url: str, headers: dict[str, str] | None = None, *, verbose: bool = False) -> dict:
    return request_json("GET", url, headers=headers, verbose=verbose, timeout=10)


def post_json(
    url: str,
    payload: dict,
    headers: dict[str, str] | None = None,
    *,
    verbose: bool = False,
) -> dict:
    return request_json(
        "POST",
        url,
        payload=payload,
        headers=headers,
        verbose=verbose,
        timeout=15,
    )


def normalize_base_url(base: str, suffixes: tuple[str, ...]) -> str:
    trimmed = base.rstrip("/")
    for suffix in suffixes:
        if trimmed.endswith(suffix):
            trimmed = trimmed[: -len(suffix)]
            trimmed = trimmed.rstrip("/")
            break
    return trimmed


def main() -> int:
    ap = argparse.ArgumentParser(description="Smoke test for quality gate flow.")
    ap.add_argument("--tenant-id", default="demo")
    ap.add_argument("--bundle-id", help="Target bundle_id. Defaults to current candidate alias.")
    ap.add_argument(
        "--control-base",
        default=os.getenv("CONTROL_BASE_URL", "http://localhost:8001"),
        help="Base URL for control plane (default: CONTROL_BASE_URL env or http://localhost:8001).",
    )
    ap.add_argument(
        "--runtime-base",
        default=os.getenv("RUNTIME_BASE_URL", "http://localhost:8000"),
        help="Base URL for runtime (default: RUNTIME_BASE_URL env or http://localhost:8000).",
    )
    ap.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose request details (URL, status code, response body on error).",
    )
    args = ap.parse_args()

    base = normalize_base_url(
        args.control_base,
        ("/api/v1/control/healthz", "/api/v1/control"),
    )
    runtime_base = normalize_base_url(
        args.runtime_base,
        ("/api/v1/runtime/healthz", "/api/v1/runtime"),
    )
    headers = build_headers()
    verbose = args.verbose

    print("[+] Check control healthz...")
    get_json(f"{base}/api/v1/control/healthz", headers=headers, verbose=verbose)

    print("[+] Check runtime healthz...")
    runtime_healthz = f"{runtime_base}/api/v1/runtime/healthz"
    try:
        get_json(runtime_healthz, headers=headers, verbose=verbose)
    except Exception as exc:
        base_hint = ""
        if "/api/v1/runtime" in args.runtime_base:
            base_hint = " Use the runtime host root (e.g., http://localhost:8000) for --runtime-base."
        raise RuntimeError(
            f"Runtime health check failed for {runtime_healthz}. Start runtime "
            "(e.g., `docker compose up runtime` or "
            "`uvicorn app.runtime.api.main:app --host 0.0.0.0 --port 8000`) "
            f"or point --runtime-base to the reachable host.{base_hint}"
        ) from exc

    aliases = get_json(
        f"{base}/api/v1/control/tenants/{args.tenant_id}/aliases",
        headers=headers,
        verbose=verbose,
    )
    target_bundle = args.bundle_id or aliases.get("candidate")
    if not target_bundle:
        raise RuntimeError("target bundle_id not provided and candidate alias not set")

    print(f"[+] Run quality report for tenant={args.tenant_id} bundle={target_bundle}")
    try:
        report = post_json(
            f"{base}/api/v1/control/tenants/{args.tenant_id}/bundles/{target_bundle}/quality/run",
            {},
            headers=headers,
            verbose=verbose,
        )
    except RuntimeError as exc:
        msg = str(exc).lower()
        if "connection refused" in msg or "failed to establish a new connection" in msg:
            raise RuntimeError(
                "Control could not reach runtime /ask endpoint (is runtime up and reachable?). "
                "If running via docker-compose, ensure the control service has RUNTIME_BASE_URL "
                "pointing to the runtime container (e.g., http://runtime:8000)."
            ) from exc
        raise
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
            verbose=verbose,
        )

        print("[+] Promote candidate -> current (gate enforced)...")
        post_json(
            f"{base}/api/v1/control/tenants/{args.tenant_id}/aliases/current",
            {"bundle_id": target_bundle},
            headers=headers,
            verbose=verbose,
        )
        print("[✓] Promotion succeeded.")
    finally:
        if prev_current:
            print("[+] Rollback current to previous value...")
            post_json(
                f"{base}/api/v1/control/tenants/{args.tenant_id}/aliases/current",
                {"bundle_id": prev_current},
                headers=headers,
                verbose=verbose,
            )
        if prev_candidate and prev_candidate != target_bundle:
            print("[+] Restore candidate to previous value...")
            post_json(
                f"{base}/api/v1/control/tenants/{args.tenant_id}/aliases/candidate",
                {"bundle_id": prev_candidate},
                headers=headers,
                verbose=verbose,
            )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - smoke helper
        sys.stderr.write(f"error: {exc}\n")
        raise SystemExit(1)
