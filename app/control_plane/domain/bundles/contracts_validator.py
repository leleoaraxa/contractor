from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml


@dataclass(frozen=True)
class ContractValidationError:
    code: str
    message: str
    path: str


def _load_yaml(path: Path) -> Dict[str, Any]:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    return doc or {}


def validate_ontology_intents(path: Path) -> List[ContractValidationError]:
    errs: List[ContractValidationError] = []
    doc = _load_yaml(path)

    if not isinstance(doc.get("version"), int) or doc.get("version", 0) < 1:
        errs.append(
            ContractValidationError(
                "intents.version", "version must be integer >= 1", str(path)
            )
        )

    intents = doc.get("intents")
    if not isinstance(intents, list) or not intents:
        errs.append(
            ContractValidationError(
                "intents.intents", "intents must be a non-empty list", str(path)
            )
        )
        return errs

    for i, it in enumerate(intents):
        if not isinstance(it, dict):
            errs.append(
                ContractValidationError(
                    "intents.item", f"intents[{i}] must be an object", str(path)
                )
            )
            continue
        iid = it.get("id")
        title = it.get("title")
        if not isinstance(iid, str) or not iid:
            errs.append(
                ContractValidationError(
                    "intents.id", f"intents[{i}].id must be non-empty string", str(path)
                )
            )
        if not isinstance(title, str) or not title:
            errs.append(
                ContractValidationError(
                    "intents.title",
                    f"intents[{i}].title must be non-empty string",
                    str(path),
                )
            )

    return errs


def validate_ontology_entities(path: Path) -> List[ContractValidationError]:
    errs: List[ContractValidationError] = []
    doc = _load_yaml(path)

    if not isinstance(doc.get("version"), int) or doc.get("version", 0) < 1:
        errs.append(
            ContractValidationError(
                "entities.version", "version must be integer >= 1", str(path)
            )
        )

    entities = doc.get("entities")
    if not isinstance(entities, list) or not entities:
        errs.append(
            ContractValidationError(
                "entities.entities", "entities must be a non-empty list", str(path)
            )
        )
        return errs

    for i, en in enumerate(entities):
        if not isinstance(en, dict):
            errs.append(
                ContractValidationError(
                    "entities.item", f"entities[{i}] must be an object", str(path)
                )
            )
            continue
        eid = en.get("id")
        title = en.get("title")
        if not isinstance(eid, str) or not eid:
            errs.append(
                ContractValidationError(
                    "entities.id",
                    f"entities[{i}].id must be non-empty string",
                    str(path),
                )
            )
        if not isinstance(title, str) or not title:
            errs.append(
                ContractValidationError(
                    "entities.title",
                    f"entities[{i}].title must be non-empty string",
                    str(path),
                )
            )

    return errs


def validate_ontology_terms(
    path: Path, known_intents: Set[str], known_entities: Set[str]
) -> List[ContractValidationError]:
    errs: List[ContractValidationError] = []
    doc = _load_yaml(path)

    if not isinstance(doc.get("version"), int) or doc.get("version", 0) < 1:
        errs.append(
            ContractValidationError(
                "terms.version", "version must be integer >= 1", str(path)
            )
        )

    terms = doc.get("terms")
    if not isinstance(terms, list) or not terms:
        errs.append(
            ContractValidationError(
                "terms.terms", "terms must be a non-empty list", str(path)
            )
        )
        return errs

    for i, t in enumerate(terms):
        if not isinstance(t, dict):
            errs.append(
                ContractValidationError(
                    "terms.item", f"terms[{i}] must be an object", str(path)
                )
            )
            continue

        term = t.get("term")
        intents = t.get("intents")
        entities = t.get("entities")

        if not isinstance(term, str) or not term.strip():
            errs.append(
                ContractValidationError(
                    "terms.term", f"terms[{i}].term must be non-empty string", str(path)
                )
            )

        if not isinstance(intents, list):
            errs.append(
                ContractValidationError(
                    "terms.intents", f"terms[{i}].intents must be list", str(path)
                )
            )
            intents = []

        if not isinstance(entities, list):
            errs.append(
                ContractValidationError(
                    "terms.entities", f"terms[{i}].entities must be list", str(path)
                )
            )
            entities = []

        for iid in intents:
            if isinstance(iid, str) and iid not in known_intents:
                errs.append(
                    ContractValidationError(
                        "terms.intent_ref",
                        f"terms[{i}] references unknown intent '{iid}'",
                        str(path),
                    )
                )

        for eid in entities:
            if isinstance(eid, str) and eid not in known_entities:
                errs.append(
                    ContractValidationError(
                        "terms.entity_ref",
                        f"terms[{i}] references unknown entity '{eid}'",
                        str(path),
                    )
                )

    return errs


def validate_policy_planner(path: Path) -> List[ContractValidationError]:
    errs: List[ContractValidationError] = []
    doc = _load_yaml(path)

    planner = doc.get("planner")
    if not isinstance(planner, dict):
        errs.append(
            ContractValidationError(
                "planner.root", "planner must be an object", str(path)
            )
        )
        return errs

    mm = planner.get("min_matches")
    ms = planner.get("min_score")
    on_no_match = planner.get("on_no_match")

    if not isinstance(mm, int) or mm < 0:
        errs.append(
            ContractValidationError(
                "planner.min_matches", "min_matches must be integer >= 0", str(path)
            )
        )

    if not isinstance(ms, (int, float)) or float(ms) < 0:
        errs.append(
            ContractValidationError(
                "planner.min_score", "min_score must be number >= 0", str(path)
            )
        )

    if not isinstance(on_no_match, dict):
        errs.append(
            ContractValidationError(
                "planner.on_no_match", "on_no_match must be an object", str(path)
            )
        )
        return errs

    if (
        "reason" not in on_no_match
        or not isinstance(on_no_match.get("reason"), str)
        or not on_no_match.get("reason")
    ):
        errs.append(
            ContractValidationError(
                "planner.on_no_match.reason",
                "reason must be non-empty string",
                str(path),
            )
        )

    # intent/entity may be null or string
    for k in ("intent", "entity"):
        v = on_no_match.get(k)
        if v is not None and not isinstance(v, str):
            errs.append(
                ContractValidationError(
                    f"planner.on_no_match.{k}", f"{k} must be null or string", str(path)
                )
            )

    return errs


def validate_bundle_contracts(
    bundle_dir: Path, ontology_dir: str, policies_dir: str
) -> List[ContractValidationError]:
    errs: List[ContractValidationError] = []

    o_dir = bundle_dir / ontology_dir
    p_dir = bundle_dir / policies_dir

    intents_path = o_dir / "intents.yaml"
    entities_path = o_dir / "entities.yaml"
    terms_path = o_dir / "terms.yaml"
    planner_path = p_dir / "planner.yaml"

    # validate ontology files existence (contract-level, not just structural)
    for p in (intents_path, entities_path, terms_path):
        if not p.exists():
            errs.append(
                ContractValidationError(
                    "file.missing", f"missing required file {p.name}", str(p)
                )
            )

    if intents_path.exists():
        errs.extend(validate_ontology_intents(intents_path))

    known_intents: Set[str] = set()
    if intents_path.exists():
        doc = _load_yaml(intents_path)
        for it in doc.get("intents") or []:
            if isinstance(it, dict) and isinstance(it.get("id"), str):
                known_intents.add(it["id"])

    if entities_path.exists():
        errs.extend(validate_ontology_entities(entities_path))

    known_entities: Set[str] = set()
    if entities_path.exists():
        doc = _load_yaml(entities_path)
        for en in doc.get("entities") or []:
            if isinstance(en, dict) and isinstance(en.get("id"), str):
                known_entities.add(en["id"])

    if terms_path.exists():
        errs.extend(
            validate_ontology_terms(
                terms_path, known_intents=known_intents, known_entities=known_entities
            )
        )

    # planner policy is optional in Stage 1, but if present must validate
    if planner_path.exists():
        errs.extend(validate_policy_planner(planner_path))

    return errs
