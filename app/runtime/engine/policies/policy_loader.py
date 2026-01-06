# app/runtime/engine/policies/policy_loader.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


@dataclass(frozen=True)
class PlannerPolicy:
    min_matches: int = 1
    min_score: float = 1.0
    on_no_match_intent: Optional[str] = None
    on_no_match_entity: Optional[str] = None
    on_no_match_reason: str = "no_match"


@dataclass(frozen=True)
class CachePolicy:
    enabled: bool = True
    default_ttl_seconds: int = 30
    max_ttl_seconds: int = 300


class PolicyLoaderError(RuntimeError):
    pass


class PolicyLoader:
    def load_planner_policy(self, bundle_dir: str, policies_dir: str) -> PlannerPolicy:
        base = Path(bundle_dir) / policies_dir
        path = base / "planner.yaml"
        if not path.exists():
            # Policy opcional: se não existe, usa defaults
            return PlannerPolicy()

        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        planner = doc.get("planner") or {}

        on_no_match = planner.get("on_no_match") or {}

        return PlannerPolicy(
            min_matches=int(planner.get("min_matches", 1)),
            min_score=float(planner.get("min_score", 1.0)),
            on_no_match_intent=on_no_match.get("intent", None),
            on_no_match_entity=on_no_match.get("entity", None),
            on_no_match_reason=str(on_no_match.get("reason", "no_match")),
        )

    def load_cache_policy(self, bundle_dir: str, policies_dir: str) -> CachePolicy:
        base = Path(bundle_dir) / policies_dir
        path = base / "cache.yaml"
        if not path.exists():
            return CachePolicy()

        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        cache_cfg = doc.get("cache") or {}

        enabled = bool(cache_cfg.get("enabled", True))
        default_ttl = int(cache_cfg.get("default_ttl_seconds", 30))
        max_ttl = int(cache_cfg.get("max_ttl_seconds", max(default_ttl, 30)))
        max_ttl = max(max_ttl, default_ttl)

        return CachePolicy(
            enabled=enabled,
            default_ttl_seconds=default_ttl,
            max_ttl_seconds=max_ttl,
        )
