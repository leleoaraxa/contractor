# app/runtime/engine/contracts/models.py
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class Plan(BaseModel):
    action: str = "noop"
    intent_id: Optional[str] = None
    entity_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    rationale: Optional[str] = None


class ExecutionResult(BaseModel):
    status: str
    data: Any = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class CacheMeta(BaseModel):
    cache_key: Optional[str] = None
    cache_hit: bool = False
    backend: str = "memory"
    ttl_seconds: Optional[int] = None
    latency_ms: Optional[float] = None
    bypassed: bool = False
    metrics: Dict[str, Any] = Field(default_factory=dict)


class FormatterOutput(BaseModel):
    answer: str
    meta: Dict[str, Any]
