# app/runtime/engine/ask_handler.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException

from app.runtime.engine.ask_models import AskRequest, AskResponse
from app.runtime.engine.builder.builder import Builder
from app.runtime.engine.cache.rt_cache import RuntimeCache
from app.runtime.engine.context.artifact_loader import (
    ArtifactLoader,
    ArtifactLoaderError,
)
from app.runtime.engine.context.control_plane_client import ControlPlaneClient
from app.runtime.engine.context.tenant_context import TenantContext
from app.runtime.engine.executor.postgres import PostgresExecution, PostgresExecutor
from app.runtime.engine.formatter.formatter import Formatter
from app.runtime.engine.ontology.ontology_loader import OntologyLoader
from app.runtime.engine.planner.planner import Planner
from app.runtime.engine.policies.policy_loader import (
    CachePolicy,
    PolicyLoader,
    RateLimitPolicy,
)
from app.runtime.engine.data_residency import apply_residency_contract
from app.runtime.engine.runtime_identity import apply_runtime_identity
from app.shared.errors import error_payload
from app.shared.security.rate_limit import enforce_rate_limit


@dataclass(frozen=True)
class AskPreparation:
    req: AskRequest
    explain_enabled: bool
    bundle_id: str
    manifest: Dict[str, Any]
    ctx: TenantContext
    plan: Any
    decision: Dict[str, Any]
    cache_service: RuntimeCache
    cache_meta: Any
    canonical_payload: Dict[str, Any]
    release_alias: Optional[str]


def _compact_decision(full: Dict[str, Any]) -> Dict[str, Any]:
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
        "explain": {"enabled": False},
    }


def _build_cached_response(
    cached_payload: Dict[str, Any], cache_meta: Any, explain_enabled: bool
) -> AskResponse:
    cache_meta.cache_hit = True
    cached_meta = cached_payload.get("meta") or {}
    cache_dump = cache_meta.model_dump(exclude_none=True)
    if not explain_enabled:
        cache_dump.pop("metrics", None)
        cache_dump.pop("cache_key", None)
    cached_meta["cache"] = cache_dump
    apply_runtime_identity(cached_meta)
    apply_residency_contract(cached_meta)
    return AskResponse(answer=cached_payload.get("answer", ""), meta=cached_meta)


def prepare_ask(req: AskRequest, explain_enabled: bool) -> Tuple[Optional[AskResponse], AskPreparation]:
    # 1) Resolve bundle_id deterministically
    bundle_id = req.bundle_id
    if not bundle_id:
        cp = ControlPlaneClient()
        res = cp.resolve_bundle_id(req.tenant_id, req.release_alias)
        bundle_id = res.bundle_id
        if not bundle_id:
            raise HTTPException(
                status_code=404,
                detail=error_payload(
                    error="bundle_id_missing",
                    type="not_found",
                    message="bundle id not provided and alias not set",
                    details={
                        "control_plane": {
                            "url": res.url,
                            "status": res.status,
                            "detail": res.detail,
                        }
                    },
                ),
            )

    # 2) Load manifest (bundle registry)
    loader = ArtifactLoader()
    try:
        manifest = loader.load_manifest(req.tenant_id, bundle_id)
    except ArtifactLoaderError as e:
        raise HTTPException(
            status_code=404,
            detail=error_payload(
                error="manifest_not_found",
                type="not_found",
                message=str(e),
            ),
        )

    ctx = TenantContext(tenant_id=req.tenant_id, bundle_id=bundle_id)
    policy_loader = PolicyLoader()

    bundle_dir = manifest.get("_bundle_dir")
    paths = manifest.get("paths") or {}
    ontology_dir = paths.get("ontology_dir")
    policies_dir = paths.get("policies_dir")

    rate_limit_policy = (
        policy_loader.load_rate_limit_policy(bundle_dir=bundle_dir, policies_dir=policies_dir)
        if bundle_dir and policies_dir
        else RateLimitPolicy(enabled=False, rps=0, burst=0)
    )
    if rate_limit_policy.enabled and rate_limit_policy.rps > 0 and rate_limit_policy.burst > 0:
        enforce_rate_limit(
            req.tenant_id,
            "runtime.ask",
            rps=rate_limit_policy.rps,
            burst=rate_limit_policy.burst,
        )

    # 3) Start with a stable fallback decision (always valid schema)
    decision_full: Dict[str, Any] = {
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
            ontology = OntologyLoader().load(bundle_dir=bundle_dir, ontology_dir=ontology_dir)
            policy = policy_loader.load_planner_policy(
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

    plan = Builder().build(req.question, decision, ctx)
    cache_policy = (
        policy_loader.load_cache_policy(bundle_dir=bundle_dir, policies_dir=policies_dir)
        if bundle_dir and policies_dir
        else CachePolicy()
    )
    cache_service = RuntimeCache(ctx, cache_policy)
    canonical_payload = {
        "question": req.question,
        "plan": plan.model_dump(),
        "decision": {
            "intent": decision.get("intent"),
            "entity": decision.get("entity"),
            "reason": decision.get("reason"),
        },
        "explain": explain_enabled,
    }
    cached_payload, cache_meta = cache_service.read(canonical_payload)

    release_alias = req.release_alias if not req.bundle_id else None

    if cached_payload:
        return _build_cached_response(cached_payload, cache_meta, explain_enabled), AskPreparation(
            req=req,
            explain_enabled=explain_enabled,
            bundle_id=bundle_id,
            manifest=manifest,
            ctx=ctx,
            plan=plan,
            decision=decision,
            cache_service=cache_service,
            cache_meta=cache_meta,
            canonical_payload=canonical_payload,
            release_alias=release_alias,
        )

    return None, AskPreparation(
        req=req,
        explain_enabled=explain_enabled,
        bundle_id=bundle_id,
        manifest=manifest,
        ctx=ctx,
        plan=plan,
        decision=decision,
        cache_service=cache_service,
        cache_meta=cache_meta,
        canonical_payload=canonical_payload,
        release_alias=release_alias,
    )


def execute_prepared_ask(prep: AskPreparation) -> AskResponse:
    if prep.plan.action == "noop" or not prep.plan.entity_id:
        execution = PostgresExecution(
            status="skipped",
            query=None,
            params={},
            results=[],
            row_count=0,
            error="no entity selected for execution",
            meta={"executor": "postgres", "skipped": True},
        )
    else:
        executor = PostgresExecutor()
        execution = executor.execute(prep.plan, prep.ctx)

    formatter = Formatter()
    formatted = formatter.format(
        question=prep.req.question,
        plan=prep.plan,
        decision=prep.decision,
        execution=execution,
        ctx=prep.ctx,
        manifest=prep.manifest,
        cache_meta=prep.cache_meta,
        explain_enabled=prep.explain_enabled,
        release_alias=prep.release_alias,
    )

    final_cache_meta = prep.cache_service.write(
        canonical_payload=prep.canonical_payload,
        value=formatted.model_dump(),
        cache_meta=prep.cache_meta,
    )
    formatted.meta["cache"] = final_cache_meta.model_dump(exclude_none=True)
    apply_runtime_identity(formatted.meta)
    apply_residency_contract(formatted.meta)

    return AskResponse(answer=formatted.answer, meta=formatted.meta)


def handle_ask(req: AskRequest, explain_enabled: bool) -> AskResponse:
    cached_response, prep = prepare_ask(req, explain_enabled)
    if cached_response:
        return cached_response
    return execute_prepared_ask(prep)
