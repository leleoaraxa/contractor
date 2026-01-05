#!/usr/bin/env python3
# scripts/quality/run_routing_suite.py
from __future__ import annotations

import argparse
import json
from urllib import request, error


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/json"}
    )
    try:
        with request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        # Preserve server detail to make suites debug-friendly
        try:
            body = e.read().decode("utf-8")
        except Exception:
            body = ""
        raise RuntimeError(f"HTTP {e.code} calling {url}: {body}") from e
    except Exception as e:
        raise RuntimeError(f"Error calling {url}: {e}") from e


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8000")
    ap.add_argument("--suite", default="data/quality/suites/demo_routing_suite.json")
    args = ap.parse_args()

    suite = json.loads(open(args.suite, "r", encoding="utf-8").read())
    tenant_id = suite["tenant_id"]
    release_alias = suite.get("release_alias", "current")

    ok = 0
    total = 0
    failures = []

    for case in suite["cases"]:
        total += 1
        payload = {
            "tenant_id": tenant_id,
            "release_alias": release_alias,
            "question": case["question"],
        }

        res = post_json(f"{args.base_url}/api/v1/runtime/ask", payload)
        decision = (res.get("meta") or {}).get("decision") or {}

        got_intent = decision.get("intent")
        got_entity = decision.get("entity")
        got_reason = decision.get("reason")

        exp = case["expected"]
        exp_intent = exp.get("intent")
        exp_entity = exp.get("entity")
        exp_reason = exp.get("reason", "__SKIP__")  # backward compatible

        intent_ok = got_intent == exp_intent
        entity_ok = got_entity == exp_entity
        reason_ok = True if exp_reason == "__SKIP__" else (got_reason == exp_reason)

        if intent_ok and entity_ok and reason_ok:
            ok += 1
        else:
            failures.append(
                {
                    "id": case["id"],
                    "question": case["question"],
                    "expected": exp,
                    "got": {
                        "intent": got_intent,
                        "entity": got_entity,
                        "reason": got_reason,
                    },
                }
            )

    report = {
        "suite_id": suite.get("suite_id"),
        "passed": ok,
        "total": total,
        "failures": failures,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok == total else 2


if __name__ == "__main__":
    raise SystemExit(main())
