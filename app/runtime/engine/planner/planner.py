from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.runtime.engine.ontology.ontology_loader import OntologyBundle


@dataclass(frozen=True)
class PlannerDecision:
    intent_id: Optional[str]
    entity_id: Optional[str]
    score: float
    matched_terms: List[str]
    intent_scores: Dict[str, float]
    entity_scores: Dict[str, float]


class Planner:
    """
    Stage 1 v1: deterministic scoring by exact term matches.
    - tokenize by simple split
    - match against terms.yaml (lowercased)
    - each matched term contributes +1 to linked intent/entity
    """

    def decide(self, question: str, ontology: OntologyBundle) -> PlannerDecision:
        q = (question or "").lower()
        tokens = [tok.strip(" ,.;:!?()[]{}\"'") for tok in q.split()]
        tokens = [t for t in tokens if t]

        intent_scores: Dict[str, float] = {}
        entity_scores: Dict[str, float] = {}
        matched_terms: List[str] = []

        term_map = {tm.term: tm for tm in ontology.terms}
        for tok in tokens:
            tm = term_map.get(tok)
            if not tm:
                continue
            matched_terms.append(tok)
            for iid in tm.intents:
                intent_scores[iid] = intent_scores.get(iid, 0.0) + 1.0
            for eid in tm.entities:
                entity_scores[eid] = entity_scores.get(eid, 0.0) + 1.0

        def _top(d: Dict[str, float]) -> Tuple[Optional[str], float]:
            if not d:
                return None, 0.0
            # deterministic tie-break: sort by (-score, id)
            best_id, best_score = sorted(d.items(), key=lambda kv: (-kv[1], kv[0]))[0]
            return best_id, best_score

        intent_id, intent_score = _top(intent_scores)
        entity_id, entity_score = _top(entity_scores)

        # score: mean of top intent/entity scores (0..)
        score = 0.0
        if intent_id or entity_id:
            score = (intent_score + entity_score) / 2.0

        return PlannerDecision(
            intent_id=intent_id,
            entity_id=entity_id,
            score=score,
            matched_terms=matched_terms,
            intent_scores=intent_scores,
            entity_scores=entity_scores,
        )
