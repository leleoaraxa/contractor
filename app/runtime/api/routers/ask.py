# app/runtime/api/routers/ask.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.runtime.engine.context.artifact_loader import (
    ArtifactLoader,
    ArtifactLoaderError,
)
from app.runtime.engine.context.tenant_context import TenantContext
from app.runtime.engine.context.control_plane_client import ControlPlaneClient
from app.runtime.engine.ontology.ontology_loader import OntologyLoader
from app.runtime.engine.planner.planner import Planner
from app.runtime.engine.policies.policy_loader import PolicyLoader

router = APIRouter()


class AskRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1, pattern=r"^[A-Za-z0-9._-]+$")
    question: str = Field(..., min_length=1)
    conversation_id: str | None = None
    client_id: str | None = None

    # Stage 0+: allow explicit bundle_id OR release_alias resolution (default current)
    bundle_id: str | None = None
    release_alias: str = Field(default="current", pattern="^(draft|candidate|current)$")


class AskResponse(BaseModel):
    answer: str
    meta: dict


def _compact_decision(full: dict) -> dict:
    """
    Keep schema stable, reduce payload by default.
    Always return: intent, entity, score, reason, thresholds, explain
    """
    return {
        "intent": full.get("intent"),
        "entity": full.get("entity"),
        "score": full.get("score", 0.0),
        "reason": full.get("reason", "unknown"),
        "thresholds": full.get("thresholds", {"min_matches": 0.0, "min_score": 0.0}),
        "explain": full.get("explain", {"stage": "mvp", "note": "", "enabled": False}),
    }


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, request: Request) -> AskResponse:
    x_explain = (request.headers.get("X-Explain") or "").strip().lower()
    explain_enabled = x_explain in {"1", "true", "yes", "y", "on"}

    # 1) Resolve bundle_id deterministically
    bundle_id = req.bundle_id
    if not bundle_id:
        cp = ControlPlaneClient()
        res = cp.resolve_bundle_id(req.tenant_id, req.release_alias)
        bundle_id = res.bundle_id
        if not bundle_id:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "bundle_id not provided and alias not set",
                    "control_plane": {
                        "url": res.url,
                        "status": res.status,
                        "detail": res.detail,
                    },
                },
            )

    # 2) Load manifest (bundle registry)
    loader = ArtifactLoader()
    try:
        manifest = loader.load_manifest(req.tenant_id, bundle_id)
    except ArtifactLoaderError as e:
        raise HTTPException(status_code=404, detail=str(e))

    ctx = TenantContext(tenant_id=req.tenant_id, bundle_id=bundle_id)

    bundle_dir = manifest.get("_bundle_dir")
    paths = manifest.get("paths") or {}
    ontology_dir = paths.get("ontology_dir")
    policies_dir = paths.get("policies_dir")

    # 3) Start with a stable fallback decision (always valid schema)
    decision_full: dict = {
        "intent": None,
        "entity": None,
        "score": 0.0,
        "reason": "not_implemented",
        "thresholds": {"min_matches": 0.0, "min_score": 0.0},
        "explain": {
            "stage": "mvp",
            "note": "planner not executed (missing bundle_dir/ontology_dir)",
            "enabled": explain_enabled,
        },
    }

    # 4) Try planner if we have ontology configured
    if bundle_dir and ontology_dir:
        try:
            ontology = OntologyLoader().load(
                bundle_dir=bundle_dir, ontology_dir=ontology_dir
            )
            policy = PolicyLoader().load_planner_policy(
                bundle_dir=bundle_dir, policies_dir=policies_dir
            )
            pd = Planner().decide(req.question, ontology, policy)

            decision_full = {
                # stable core
                "intent": pd.intent_id,
                "entity": pd.entity_id,
                "score": pd.score,
                "reason": pd.reason,
                "thresholds": pd.thresholds,
                "explain": {
                    "stage": "mvp",
                    "ontology_version": ontology.version,
                    "note": "planner v1 deterministic + thresholds from policies/planner.yaml",
                    "enabled": explain_enabled,
                },
            }

            # enrich only when explain is enabled
            if explain_enabled:
                decision_full.update(
                    {
                        "matched_terms": pd.matched_terms,
                        "tokens": pd.tokens,
                        "considered_terms": pd.considered_terms,
                        "intent_scores": pd.intent_scores,
                        "entity_scores": pd.entity_scores,
                        "intent_topk": {
                            "top1": pd.intent_topk.top1_id,
                            "top1_score": pd.intent_topk.top1_score,
                            "top2": pd.intent_topk.top2_id,
                            "top2_score": pd.intent_topk.top2_score,
                            "gap": pd.intent_topk.gap,
                        },
                        "entity_topk": {
                            "top1": pd.entity_topk.top1_id,
                            "top1_score": pd.entity_topk.top1_score,
                            "top2": pd.entity_topk.top2_id,
                            "top2_score": pd.entity_topk.top2_score,
                            "gap": pd.entity_topk.gap,
                        },
                    }
                )

        except Exception as e:
            # Keep stable schema on error
            decision_full = {
                "intent": None,
                "entity": None,
                "score": 0.0,
                "reason": "planner_error",
                "thresholds": {"min_matches": 0.0, "min_score": 0.0},
                "explain": {
                    "stage": "mvp",
                    "note": f"planner failed: {e}",
                    "enabled": explain_enabled,
                },
            }

    # 5) Compact by default; full only when explain enabled
    decision = decision_full if explain_enabled else _compact_decision(decision_full)

    answer = (
        "CONTRACTOR runtime is up. Planner is now active (Stage 1).\n"
        f"Decision: intent={decision.get('intent')} entity={decision.get('entity')}\n"
        f"Received question: {req.question}"
    )

    meta = {
        "tenant_id": ctx.tenant_id,
        "bundle_id": ctx.bundle_id,
        "release_alias": req.release_alias if not req.bundle_id else None,
        "manifest": {
            "created_at": manifest.get("created_at"),
            "source": manifest.get("source"),
            "checksum": manifest.get("checksum"),
        },
        "decision": decision,
        "explain_enabled": explain_enabled,
    }

    return AskResponse(answer=answer, meta=meta)
