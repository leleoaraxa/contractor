# app/runtime/engine/executor/postgres.py
from __future__ import annotations

import os
from typing import Any

import psycopg2
from pydantic import BaseModel, Field

from app.runtime.engine.context.tenant_context import TenantContext
from app.runtime.engine.contracts.models import Plan


class SQLQuery(BaseModel):
    query: str
    params: dict


class SQLBuilder:
    def build(self, entity_id: str, intent_id: str | None = None) -> SQLQuery:
        # NOTE: This is a very basic implementation for Stage 0.
        # It does not support joins, filters, or aggregations yet.
        # This will be expanded in future stages.
        if not entity_id:
            raise ValueError("entity_id is required to build a SQL query")

        query = f"SELECT * FROM {entity_id} LIMIT 10;"
        return SQLQuery(query=query, params={})


class PostgresExecution(BaseModel):
    status: str
    query: str
    params: dict
    results: list[dict]
    row_count: int
    error: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class PostgresExecutor:
    def __init__(self):
        self.sql_builder = SQLBuilder()
        self.conn_str = os.environ.get("POSTGRES_DSN")
        if not self.conn_str:
            raise ValueError("POSTGRES_DSN environment variable is not set.")

    def execute(self, plan: Plan, ctx: TenantContext) -> PostgresExecution:
        sql_query = self.sql_builder.build(entity_id=plan.entity_id)
        results = []
        row_count = 0
        error = None
        status = "ok"
        meta = {"executor": "postgres"}

        try:
            with psycopg2.connect(self.conn_str) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_query.query, sql_query.params)
                    row_count = cursor.rowcount
                    column_names = [desc[0] for desc in cursor.description]
                    for row in cursor.fetchall():
                        results.append(dict(zip(column_names, row)))
        except Exception as e:
            error = str(e)
            status = "error"

        return PostgresExecution(
            status=status,
            query=sql_query.query,
            params=sql_query.params,
            results=results,
            row_count=row_count,
            error=error,
            meta=meta,
        )
