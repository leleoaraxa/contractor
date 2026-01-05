# app/runtime/engine/ontology/ontology_loader.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


@dataclass(frozen=True)
class OntologyIntent:
    id: str
    title: str
    description: str = ""


@dataclass(frozen=True)
class OntologyEntity:
    id: str
    title: str
    description: str = ""
    kind: str = "unknown"


@dataclass(frozen=True)
class TermMapping:
    term: str
    intents: List[str]
    entities: List[str]


@dataclass(frozen=True)
class OntologyBundle:
    version: int
    intents: Dict[str, OntologyIntent]
    entities: Dict[str, OntologyEntity]
    terms: List[TermMapping]


class OntologyLoaderError(RuntimeError):
    pass


class OntologyLoader:
    def load(self, bundle_dir: str, ontology_dir: str) -> OntologyBundle:
        base = Path(bundle_dir) / ontology_dir

        intents_path = base / "intents.yaml"
        entities_path = base / "entities.yaml"
        terms_path = base / "terms.yaml"

        if not intents_path.exists():
            raise OntologyLoaderError(f"missing intents.yaml: {intents_path}")
        if not entities_path.exists():
            raise OntologyLoaderError(f"missing entities.yaml: {entities_path}")
        if not terms_path.exists():
            raise OntologyLoaderError(f"missing terms.yaml: {terms_path}")

        intents_doc = yaml.safe_load(intents_path.read_text(encoding="utf-8")) or {}
        entities_doc = yaml.safe_load(entities_path.read_text(encoding="utf-8")) or {}
        terms_doc = yaml.safe_load(terms_path.read_text(encoding="utf-8")) or {}

        version = int(
            terms_doc.get("version")
            or intents_doc.get("version")
            or entities_doc.get("version")
            or 1
        )

        intents: Dict[str, OntologyIntent] = {}
        for it in intents_doc.get("intents", []) or []:
            iid = str(it.get("id") or "").strip()
            if iid:
                intents[iid] = OntologyIntent(
                    id=iid,
                    title=str(it.get("title") or iid),
                    description=str(it.get("description") or ""),
                )

        entities: Dict[str, OntologyEntity] = {}
        for en in entities_doc.get("entities", []) or []:
            eid = str(en.get("id") or "").strip()
            if eid:
                entities[eid] = OntologyEntity(
                    id=eid,
                    title=str(en.get("title") or eid),
                    description=str(en.get("description") or ""),
                    kind=str(en.get("kind") or "unknown"),
                )

        terms: List[TermMapping] = []
        for t in terms_doc.get("terms", []) or []:
            term = str(t.get("term") or "").strip().lower()
            if not term:
                continue
            terms.append(
                TermMapping(
                    term=term,
                    intents=[str(x) for x in (t.get("intents") or [])],
                    entities=[str(x) for x in (t.get("entities") or [])],
                )
            )

        return OntologyBundle(
            version=version, intents=intents, entities=entities, terms=terms
        )
