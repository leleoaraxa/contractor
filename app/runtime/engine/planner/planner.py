# app/runtime/engine/planner/planner.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from app.runtime.engine.ontology.ontology_loader import OntologyBundle
from app.runtime.engine.policies.policy_loader import PlannerPolicy


@dataclass(frozen=True)
class TopK:
    top1_id: Optional[str]
    top1_score: float
    top2_id: Optional[str]
    top2_score: float
    gap: float


@dataclass(frozen=True)
class PlannerDecision:
    intent_id: Optional[str]
    entity_id: Optional[str]
    score: float
    matched_terms: List[str]

    # richer explain
    tokens: List[str]
    considered_terms: List[str]
    intent_scores: Dict[str, float]
    entity_scores: Dict[str, float]
    intent_topk: TopK
    entity_topk: TopK
    thresholds: Dict[str, float]
    reason: str


class Planner:
    """
    Stage 1.1 v1:
    - deterministic scoring by exact term matches
    - thresholds via PlannerPolicy (yaml-driven)
    - top2 + gap for intent/entity
    - explicit no-match reason
    """

    def decide(
        self, question: str, ontology: OntologyBundle, policy: PlannerPolicy
    ) -> PlannerDecision:
        q = (question or "").lower()
        tokens = [tok.strip(" ,.;:!?()[]{}\"'") for tok in q.split()]
        tokens = [t for t in tokens if t]

        intent_scores: Dict[str, float] = {}
        entity_scores: Dict[str, float] = {}
        matched_terms: List[str] = []

        # deterministic term map
        term_map = {tm.term: tm for tm in ontology.terms}
        considered_terms = sorted(term_map.keys())

        for tok in tokens:
            tm = term_map.get(tok)
            if not tm:
                continue
            matched_terms.append(tok)
            for iid in tm.intents:
                intent_scores[iid] = intent_scores.get(iid, 0.0) + 1.0
            for eid in tm.entities:
                entity_scores[eid] = entity_scores.get(eid, 0.0) + 1.0

        def _top2(d: Dict[str, float]) -> TopK:
            if not d:
                return TopK(None, 0.0, None, 0.0, 0.0)
            items = sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))  # deterministic tie-break
            top1_id, top1_score = items[0]
            if len(items) > 1:
                top2_id, top2_score = items[1]
            else:
                top2_id, top2_score = None, 0.0
            gap = float(top1_score - top2_score)
            return TopK(top1_id, float(top1_score), top2_id, float(top2_score), gap)

        intent_topk = _top2(intent_scores)
        entity_topk = _top2(entity_scores)

        # score = mean of top1 intent/entity scores
        score = 0.0
        if intent_topk.top1_id or entity_topk.top1_id:
            score = (intent_topk.top1_score + entity_topk.top1_score) / 2.0

        thresholds = {
            "min_matches": float(policy.min_matches),
            "min_score": float(policy.min_score),
        }
        passes = (len(matched_terms) >= policy.min_matches) and (score >= policy.min_score)

        if not passes:
            # No-match policy (yaml-driven)
            return PlannerDecision(
                intent_id=policy.on_no_match_intent,
                entity_id=policy.on_no_match_entity,
                score=score,
                matched_terms=matched_terms,
                tokens=tokens,
                considered_terms=considered_terms,
                intent_scores=intent_scores,
                entity_scores=entity_scores,
                intent_topk=intent_topk,
                entity_topk=entity_topk,
                thresholds=thresholds,
                reason=policy.on_no_match_reason,
            )

        return PlannerDecision(
            intent_id=intent_topk.top1_id,
            entity_id=entity_topk.top1_id,
            score=score,
            matched_terms=matched_terms,
            tokens=tokens,
            considered_terms=considered_terms,
            intent_scores=intent_scores,
            entity_scores=entity_scores,
            intent_topk=intent_topk,
            entity_topk=entity_topk,
            thresholds=thresholds,
            reason="ok",
        )
