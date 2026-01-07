# app/runtime/engine/formatter/formatter.py
from __future__ import annotations

from typing import Any, Dict

from app.runtime.engine.context.tenant_context import TenantContext
from app.runtime.engine.contracts.models import (
    CacheMeta,
    ExecutionResult,
    FormatterOutput,
    Plan,
)


class Formatter:
    """
    Stage 1 formatter (stub).
    Produces a stable textual answer and structured meta without leaking internal fields.
    """

    def format(
        self,
        question: str,
        plan: Plan,
        decision: Dict[str, Any],
        execution: ExecutionResult,
        ctx: TenantContext,
        manifest: Dict[str, Any],
        cache_meta: CacheMeta,
        explain_enabled: bool,
        release_alias: str | None,
    ) -> FormatterOutput:
        answer_lines = [
            "CONTRACTOR runtime pipeline is up (Stage 1 skeleton).",
            f"Action: {plan.action} -> {execution.status}",
            f"Received question: {question}",
        ]
        answer = "\n".join(answer_lines)

        cache_dump = cache_meta.model_dump()
        if not explain_enabled:
            cache_dump.pop("metrics", None)
            cache_dump.pop("cache_key", None)

        execution_dump = {
            "status": execution.status,
            "row_count": execution.row_count,
            "results": execution.results,
        }
        if explain_enabled:
            execution_dump["query"] = execution.query
            execution_dump["params"] = execution.params
            if execution.error:
                execution_dump["error"] = execution.error
            if execution.meta:
                execution_dump["meta"] = execution.meta

        plan_dump = plan.model_dump()
        if not explain_enabled:
            plan_dump.pop("rationale", None)

        formatted_meta: Dict[str, Any] = {
            "tenant_id": ctx.tenant_id,
            "bundle_id": ctx.bundle_id,
            "release_alias": release_alias,
            "manifest": {
                "created_at": manifest.get("created_at"),
                "source": manifest.get("source"),
                "checksum": manifest.get("checksum"),
            },
            "decision": decision,
            "plan": plan_dump,
            "execution": execution_dump,
            "cache": cache_dump,
            "explain_enabled": explain_enabled,
        }

        if explain_enabled:
            formatted_meta["builder"] = {"rationale": plan.rationale}

        return FormatterOutput(answer=answer, meta=formatted_meta)
