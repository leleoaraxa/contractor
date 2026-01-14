# Evidence — Stage 3 Rollback Production Validation (ADR 0028)

## Context

This evidence record targets **ADR 0028 — Stage 3 Checklist, item 5: Rollback & Recovery** ("Rollback completo validado em produção" and "Evidência de teste de rollback"). The rollback mechanism in scope is the **manual alias swap** documented in `docs/RUNBOOKS/rollback.md`, which uses the Control Plane `aliases/current` endpoint with bundle validation and resolves via `versions/current/resolve`.

## Environment & Preconditions

**Expected production prerequisites (per ADR/runbooks):**
- Control Plane reachable at `http://localhost:8001`
- Runtime reachable at `http://localhost:8000`
- Bundle registry available with at least one prior bundle
- Active tenant with `current` alias set

**Actual environment (this execution):**
- No Control Plane/Runtime services reachable in the execution environment.

## Steps Executed (real commands)

Timestamp (UTC): `2026-01-14 18:18:59` (from `date -u`)

### 1) Control Plane health check
```bash
curl -s -S http://localhost:8001/api/v1/control/healthz
```
**Output:**
```
curl: (7) Failed to connect to localhost port 8001 after 0 ms: Couldn't connect to server
```

### 2) Runtime health check
```bash
curl -s -S http://localhost:8000/api/v1/runtime/healthz
```
**Output:**
```
curl: (7) Failed to connect to localhost port 8000 after 0 ms: Couldn't connect to server
```

### 3) Resolve current bundle (required for rollback baseline)
```bash
curl -s -S http://localhost:8001/api/v1/control/tenants/demo/resolve/current
```
**Output:**
```
curl: (7) Failed to connect to localhost port 8001 after 0 ms: Couldn't connect to server
```

## Expected Rollback Flow (not executed due to missing production runtime)

Per `docs/RUNBOOKS/rollback.md`, the rollback would proceed as:
1) Resolve current bundle for tenant.
2) Validate prior bundle via `/bundles/{bundle_id}/validate`.
3) Reassign `aliases/current` to prior bundle.
4) Re-resolve alias and validate runtime health.

## Evidence Summary

| Evidence item | Status | Notes |
| --- | --- | --- |
| Timestamp of rollback | **Missing** | No rollback executed due to unavailable services. |
| Bundle ID reverted | **Missing** | No control plane connectivity. |
| Alias before/after | **Missing** | Alias endpoints unreachable. |
| Control/Runtime logs | **Missing** | No services running to emit logs. |
| Post-rollback health check | **Missing** | Control Plane/Runtime health checks failed to connect. |

## Result

**Rollback validated in production:** **NÃO**

## Limitations / Blocking Factors

- **No production Control Plane or Runtime available** in the execution environment, so the required rollback endpoints and health checks are unreachable.
- Without a real running tenant/bundle, the rollback process cannot be executed or evidenced as required by ADR 0028.

