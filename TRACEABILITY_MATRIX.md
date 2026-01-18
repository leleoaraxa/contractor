# TRACEABILITY MATRIX — CONTRACTOR

## 1. ADR → Código → Teste → Evidência

| ADR | Requisito Resumido | Código (Paths) | Testes (Paths) | Evidência (Paths) | Status | Observações |
| --- | --- | --- | --- | --- | --- | --- |
| 0001 | Separação Control/Data Plane | `app/control_plane/`, `app/runtime/` | `tests/integration/test_e2e_flow.py` | `docs/FOUNDATION.md` | OK | Estrutural |
| 0002 | Versionamento de Artefatos | `app/control_plane/domain/artifacts/` | `tests/integration/test_promotion_gates.py` | `docs/ADR/0002-artifact-versioning-model.md` | OK | |
| 0003 | Isolamento Multi-tenant | `app/shared/security/auth.py` | `tests/integration/test_control_plane_tenant_scope.py` | `docs/ADR/0003-multi-tenant-isolation-model.md` | OK | |
| 0007 | Baseline de Segurança | `app/shared/security/auth.py`, `redact.py` | `tests/integration/test_runtime_logs_no_payload.py` | `docs/SECURITY.md` | OK | |
| 0013 | Rate Limiting | `app/shared/security/rate_limit.py` | `tests/integration/test_promotion_gates.py` | `docs/ADR/0013-rate-limiting...` | OK | |
| 0022 | Runtime Dedicado | `app/runtime/api/routers/ask.py` | `tests/integration/test_dedicated_runtime_mode.py` | `docs/ADR/0022-...` | OK | |
| 0024 | Observabilidade Tenant | `app/runtime/api/metrics.py` | `tests/integration/test_runtime_tenant_observability.py` | `ops/observability/dashboards/` | OK | |
| 0026 | Data Residency | `app/runtime/engine/data_residency.py` | `tests/integration/test_runtime_data_residency.py` | `docs/ADR/0026-...` | OK | |
| 0027 | Identity Boundaries | `app/shared/security/auth.py` | `tests/integration/test_runtime_access_control.py` | `docs/ADR/0027-...` | OK | |

---

## 2. Endpoint Inventory

### Control Plane
| Method | Path | Handler | Auth | Rate Limit | Contratos | Testes |
| --- | --- | --- | --- | --- | --- | --- |
| GET | `/api/v1/control/healthz` | `healthz.py` | Sim | Sim | — | `test_e2e_flow.py` |
| GET | `/tenants/{id}/bundles/{bid}/validate` | `bundles.py` | Sim | Sim | `manifest.schema.yaml` | `test_bundle_contract_validation.py` |
| POST | `/tenants/{id}/bundles/{bid}/quality/run` | `quality.py` | Sim | Sim | — | `test_promotion_gates.py` |
| POST | `/tenants/{id}/aliases/{alias}` | `versions.py` | Sim | Sim | — | `test_promotion_gates.py` |

### Runtime
| Method | Path | Handler | Auth | Rate Limit | Contratos | Testes |
| --- | --- | --- | --- | --- | --- | --- |
| POST | `/api/v1/runtime/ask` | `ask.py` | Sim | Sim | — | `test_dedicated_runtime_mode.py` |
| GET | `/api/v1/runtime/ask/result/{id}` | `ask.py` | Sim | Sim | — | `test_async_worker_flow.py` |
| GET | `/api/v1/runtime/healthz` | `healthz.py` | Sim | Sim | — | `test_e2e_flow.py` |

---

## 3. Policy/Schema Coverage

| Schema/Policy | Onde é carregado/validado | Fallback Behavior | Testes |
| --- | --- | --- | --- |
| `manifest.schema.yaml` | `app/control_plane/domain/bundles/validator.py` (Manual) | Fail validation | `test_bundle_contract_validation.py` |
| `entities.schema.yaml` | `contracts_validator.py` (Manual) | Fail validation | `test_bundle_contract_validation.py` |
| `runtime.schema.yaml` | `contracts_validator.py` (Manual) | Fail validation | `test_promotion_gates.py` |
| `planner.schema.yaml` | `contracts_validator.py` (Manual) | Fail validation | `test_promotion_gates.py` |
| `output.schema.yaml` | `contracts_validator.py` (Manual) | Fail validation | `test_promotion_gates.py` |
