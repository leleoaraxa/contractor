# app/runtime/engine/executor/executor.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional

from app.runtime.engine.context.tenant_context import TenantContext
from app.runtime.engine.contracts.models import ExecutionResult, Plan


class Executor(ABC):
    @abstractmethod
    def execute(
        self, plan: Plan, ctx: TenantContext
    ) -> ExecutionResult:  # pragma: no cover - interface
        raise NotImplementedError


class NoopExecutor(Executor):
    """
    ADR 0005 placeholder executor.
    Returns a structured not_implemented result without performing any I/O.
    """

    def execute(self, plan: Plan, ctx: TenantContext) -> ExecutionResult:
        data = {
            "action": plan.action,
            "intent_id": plan.intent_id,
            "entity_id": plan.entity_id,
            "tenant_id": ctx.tenant_id,
            "bundle_id": ctx.bundle_id,
        }
        return ExecutionResult(status="not_implemented", data=data, meta={"executor": "noop"})


class DirectPostgresExecutor(Executor):
    """
    Interface placeholder for ADR 0005.
    Execution logic will be implemented once connectivity contracts are finalized.
    """

    def __init__(self, connection_params: Optional[Dict] = None) -> None:
        self.connection_params = connection_params or {}

    def execute(self, plan: Plan, ctx: TenantContext) -> ExecutionResult:
        raise NotImplementedError("DirectPostgresExecutor is not implemented yet")
