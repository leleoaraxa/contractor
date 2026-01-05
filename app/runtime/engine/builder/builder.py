# app/runtime/engine/builder/builder.py
from __future__ import annotations

from typing import Dict

from app.runtime.engine.context.tenant_context import TenantContext
from app.runtime.engine.contracts.models import Plan


class Builder:
    """
    Stage 1 runtime builder (stub).

    Converts a planner decision into a deterministic Plan.
    No domain heuristics are applied; action is constrained to "noop" for now.
    """

    def build(self, question: str, decision: Dict, ctx: TenantContext) -> Plan:
        action = "noop"
        parameters = {
            "question_fingerprint": (question or "").strip(),
            "reason": decision.get("reason"),
        }
        intent_id = decision.get("intent")
        entity_id = decision.get("entity")

        rationale = (
            "deterministic noop plan (Stage 1 runtime skeleton: planner -> builder)"
        )

        return Plan(
            action=action,
            intent_id=intent_id,
            entity_id=entity_id,
            parameters=parameters,
            rationale=rationale,
        )
