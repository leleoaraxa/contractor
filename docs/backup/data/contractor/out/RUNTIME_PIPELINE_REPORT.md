# Runtime Pipeline Report (Stage 1 Skeleton)

## Overview
The runtime `/ask` path now follows the complete Stage 1 pipeline (Ask → Context → Planner → Builder → Cache → Executor → Formatter → Cache write → Response). The implementation keeps the contract stable while introducing deterministic stubs for plan creation, execution, formatting, and policy-driven caching (ADR 0005, 0008, 0011).

## Architecture
- **Context**: bundle resolution + tenant context (`TenantContext`).
- **Planner**: deterministic ontology-based router with optional explain.
- **Builder (stub)**: converts planner decision into a deterministic `Plan` with action `noop`.
- **Cache (ADR 0008)**:
  - Key = `tenant_id` + `bundle_id` + canonical hash of request fingerprint (question + plan + decision).
  - Backend: Redis when available (config `runtime_redis_url`), fallback to in-memory LRU.
  - TTL: bundle policy (`policies/cache.yaml`), defaults to 30s/300s max.
  - Metrics: hits/misses/bypassed/errors + latency counters (in-memory).
- **Executor (stub)**: `NoopExecutor` returns `not_implemented`; `DirectPostgresExecutor` interface reserved for ADR 0005.
- **Formatter (stub)**: stable text output + structured meta with cache/executor/plan fields; explain adds builder rationale and executor data.

### Flow (mermaid)
```mermaid
flowchart LR
    A[Ask] --> B[Context\n(tenant/bundle)]
    B --> C[Planner]
    C --> D[Builder\nPlan]
    D --> E[Cache Read]
    E -- hit --> R[Response (cached)]
    E -- miss --> F[Executor\n(Noop)]
    F --> G[Formatter]
    G --> H[Cache Write]
    H --> R
```

### Cache Policy
- Location: `policies/cache.yaml` inside each bundle (schema: `contracts/policies/cache.schema.yaml`).
- Fields: `enabled`, `default_ttl_seconds`, `max_ttl_seconds`.
- When disabled or TTL=0, cache is bypassed but metrics are still recorded.

## Testing
Use the demo bundle already in the registry.

1) Start runtime (local example):
```bash
make run-runtime
```

2) Call `/ask` twice to observe cache miss then hit:
```bash
curl -sS -X POST http://localhost:8000/api/v1/runtime/ask \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"demo","release_alias":"current","question":"health status"}' | jq '.meta.cache.cache_hit'

curl -sS -X POST http://localhost:8000/api/v1/runtime/ask \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"demo","release_alias":"current","question":"health status"}' | jq '.meta.cache.cache_hit'
```
The first call should return `false` and the second `true`.

3) Quality suite (cache hit/miss):
```bash
python scripts/quality/run_routing_suite.py --suite data/quality/suites/demo_pipeline_suite.json
```

4) Optional explain:
```bash
curl -sS -X POST http://localhost:8000/api/v1/runtime/ask \
  -H "X-Explain: 1" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"demo","release_alias":"current","question":"health status"}' | jq '.meta'
```
