# app/control_plane/domain/quality/runner.py
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from urllib import error, request

from app.shared.config.settings import settings


def _utcnow() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def post_json(url: str, payload: Dict) -> Dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url, data=data, method="POST", headers={"Content-Type": "application/json"}
    )
    try:
        with request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
        except Exception:
            body = ""
        raise RuntimeError(f"HTTP {e.code} calling {url}: {body}") from e
    except Exception as e:
        raise RuntimeError(f"Error calling {url}: {e}") from e


def run_suite(base_url: str | None, suite_path: str, bundle_id: Optional[str] = None) -> Dict:
    """
    Run a routing suite against runtime /ask endpoint.

    Returns a structured result used by the Control Plane quality report.
    """
    host = settings.runtime_host or "localhost"
    if host == "0.0.0.0":
        host = "localhost"
    runtime_base = (base_url or "").rstrip("/") or (f"http://{host}:{settings.runtime_port}")
    suite = json.loads(Path(suite_path).read_text(encoding="utf-8"))

    tenant_id = suite["tenant_id"]
    release_alias = suite.get("release_alias", "current")

    ok = 0
    total = 0
    failures: List[Dict] = []
    started_at = _utcnow()

    for case in suite["cases"]:
        total += 1
        payload = {
            "tenant_id": tenant_id,
            "release_alias": release_alias,
            "question": case["question"],
        }
        if bundle_id:
            payload["bundle_id"] = bundle_id

        res = post_json(f"{runtime_base}/api/v1/runtime/ask", payload)
        decision = (res.get("meta") or {}).get("decision") or {}

        got_intent = decision.get("intent")
        got_entity = decision.get("entity")
        got_reason = decision.get("reason")

        exp = case["expected"]
        exp_intent = exp.get("intent")
        exp_entity = exp.get("entity")
        exp_reason = exp.get("reason", "__SKIP__")

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

    finished_at = _utcnow()
    status = "pass" if ok == total else "fail"

    return {
        "status": status,
        "suite_id": suite.get("suite_id"),
        "tenant_id": tenant_id,
        "release_alias": release_alias,
        "passed": ok,
        "total": total,
        "failures": failures,
        "started_at": started_at,
        "finished_at": finished_at,
        "suite_source": suite_path,
        "suite_path": str(Path(suite_path).resolve()),
    }
