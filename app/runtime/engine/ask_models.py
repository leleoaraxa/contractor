# app/runtime/engine/ask_models.py
from __future__ import annotations

from pydantic import BaseModel, Field


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
