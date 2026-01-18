# AUDIT REPORT — CONTRACTOR

## 1. Executive Snapshot

**Estado Geral:**
- **Docs:** 🟡 **WARN** (Inconsistência entre relatórios de auditoria interna e estado real; duplicidade/idioma em overviews executivos).
- **Código:** 🟢 **OK** (Aderente aos ADRs fundamentais, isolamento de tenant implementado, segurança/redação ativa).
- **Testes:** 🟢 **OK** (Boa cobertura de integração para requisitos de Stage 3, embora falte validação em produção para rollback).
- **Ops/Runbooks:** 🟢 **OK** (Runbooks detalhados, dashboards versionados (apesar de nota em auditoria prévia), métricas implementadas).

**Top 10 Achados:**

| ID | Achado | Severidade | Impacto |
| --- | --- | --- | --- |
| 1 | Drift de Contrato: Schemas YAML não são usados para validação no código. | **P0** | Inconsistência entre contrato documentado e enforcement real. |
| 2 | Inconsistência Documental: `STAGE_3_READINESS_AUDIT.md` indica falta de dashboards que existem. | **P1** | Desorientação sobre a prontidão real do projeto. |
| 3 | Observabilidade de Tenant limitada ao modo dedicado. | **P1** | Falta de visibilidade por tenant em modo compartilhado. |
| 4 | Duplicação de Documentos Executivos (PT vs EN) com conteúdos divergentes. | **P2** | Mensagem de produto inconsistente. |
| 5 | ADRs Stage 3 (0022-0027) marcados como Draft em auditoria mas Accepted nos arquivos. | **P1** | Incerteza sobre a governança técnica. |
| 6 | Retenção configurável por tenant/plano não implementada (apenas global). | **P2** | Não atende requisitos enterprise de flexibilidade. |
| 7 | Validação manual em `contracts_validator.py` menos estrita que o Schema. | **P1** | Risco de aceitação de artefatos inválidos. |
| 8 | Falta de evidência de produção para Rollback (limitação de ambiente). | **P1** | Risco operacional não validado em cenário real. |
| 9 | Redact omite chaves sensíveis em vez de apenas mascarar (comportamento seguro mas opaco). | **P2** | Dificuldade em depurar presença de campos sensíveis. |
| 10 | Métricas de SLO não usam labels de tenant (apenas globais). | **P2** | Impossibilidade de medir SLO por cliente no dashboard geral. |

---

## 2. Mapa “Onde estamos” por Stage

Ancorado em `docs/ADR/0021-...`, `docs/STATUS/*`, `docs/ADR/README.md`, `docs/ADR/STAGE_3_READINESS_AUDIT.md`.

| Stage | Prometido na doc | Evidência no repo | Implementado no código | Coberto por testes | Gap |
| --- | --- | --- | --- | --- | --- |
| **0** | Runtime/Control Plane funcional | `docs/FOUNDATION.md` | `app/control_plane`, `app/runtime` | `tests/integration/test_e2e_flow.py` | — |
| **1** | Multi-tenant pool, cache, rate limit | `docs/ADR/0003`, `0013` | `app/shared/security/rate_limit.py`, `app/runtime/executor/cache` | `tests/integration/test_promotion_gates.py` | — |
| **2** | SLOs ativos, incident management, rollback | `docs/RUNBOOKS/slo_active.md`, `rollback.md` | `app/shared/metrics.py`, `app/control_plane/domain/bundles/promoter.py` | `tests/integration/test_promotion_gates.py` | Rollback validado em non-prod apenas. |
| **3** | Runtime dedicado, residency, isolation | `docs/ADR/0022`, `0026`, `0028` | `app/runtime/api/routers/ask.py` (enforce) | `tests/integration/test_dedicated_runtime_mode.py`, `test_runtime_data_residency.py` | Dashboards versionados mas audit diz que não; falta evidência produção. |
| **4** | Marketplace, ecossistema | `docs/ADR/0029-0038` | — | — | Não iniciado (conforme roadmap). |

---

## 3. Auditoria de Documentação

- **Consistência Interna:**
  - `EXECUTIVE-OVERVIEW.md` (raiz) vs `docs/EXECUTIVE/EXECUTIVE_OVERVIEW.md`: O primeiro está em PT, o segundo em EN e com estrutura mais moderna. Sugere-se unificar ou manter tradução fiel.
  - `STAGE_3_READINESS_AUDIT.md` (2026-01-14) está defasado em relação ao estado do repo: afirma que dashboards não existem (existem em `ops/observability/dashboards/tenant/`) e que ADRs estão em Draft (estão Accepted).
- **Source of Truth:** ADRs são o source of truth claro (`docs/ADR/README.md`). Runbooks estão bem localizados e atualizados.
- **Sinalização:** Documentos normativos (ADR/Guardrails) estão claramente separados de operacionais (Runbooks).

---

## 4. Auditoria de Contratos (Schemas + Bundle Manifest + Policies)

- **Arquivos:** `contracts/bundles/manifest.schema.yaml`, `contracts/ontology/*.schema.yaml`, `contracts/policies/*.schema.yaml`.
- **Validação:** O código em `app/control_plane/domain/bundles/contracts_validator.py` NÃO utiliza os schemas. Faz validação manual (if/else).
- **Gaps:** A validação manual ignora regex (ex: padrão de ID de entidade) e `additionalProperties: false`.

| Contrato | Código que valida | Teste que cobre |
| --- | --- | --- |
| Manifest | `validator.py` | `test_bundle_contract_validation.py` |
| Ontology (Intents/Entities/Terms) | `contracts_validator.py` | `test_bundle_contract_validation.py` |
| Policies (Planner/Runtime/Output) | `contracts_validator.py` | `test_promotion_gates.py` |

---

## 5. Auditoria do Control Plane

- **Endpoints:** `bundles.py`, `quality.py`, `tenants.py`, `versions.py`, `healthz.py`.
- **Domínio:** Implementação limpa de bundles (validação/promoção), quality (runner), e tenants.
- **Segurança:** Auth via API Key (`require_api_key`) e Rate Limit (`enforce_rate_limit`) aplicados nos routers.
- **ADR Adherence:** Segue ADR 0001 (separação planes) e 0002 (versionamento).

---

## 6. Auditoria do Runtime

- **Pipeline `/ask`:** `ask.py` -> `prepare_ask` -> `execute_prepared_ask`.
- **Isolamento:** `_enforce_dedicated_tenant` e `_enforce_residency` implementados e verificados em `ask.py`.
- **Modo Dedicado:** Identidade carregada de settings em `runtime_identity.py`.
- **Segurança:** `redact.py` ativo via `JsonFormatter` em todos os logs. Bloqueio cross-tenant via `enforce_tenant_scope`.
- **Data Residency:** Enforcement real baseado em `runtime_region` e requisitos de tenant em settings.

---

## 7. Worker e Async Flow

- **Implementação:** `runtime/worker/main.py` usa BLPOP no Redis.
- **Contrato:** Suporta `X-Async` header para disparar fluxo assíncrono.
- **Métricas:** Worker emite métricas de processamento (ok/fail) e profundidade de fila.
- **Testes:** Coberto por `tests/integration/test_async_worker_flow.py`.

---

## 8. Observability / SLO / Retention

- **Dashboard:** Dashboards por tenant localizados em `ops/observability/dashboards/tenant/`.
- **SLO:** Rules em `ops/prometheus/rules/contractor_slo_rules.yaml`. Usam `http_requests_total` (geral).
- **Métricas:** `shared/metrics.py` (geral) e `runtime/api/metrics.py` (tenant-specific, apenas modo dedicado).
- **Retention:** `ops/observability/retention.yaml` define defaults. Falta implementação de override por tenant.

---

## 9. SDK Python

- **Local:** `sdk/python/**`.
- **Cobertura:** `RuntimeClient` implementa `ask` e `ask_question`. `ContractorClient` lida com auth e requests.
- **Gap:** SDK ainda não cobre todos os endpoints do Control Plane (ex: gestão de aliases/quality via SDK).

---

## 10. Testes de Integração

- **Mapeamento:**
  - `test_dedicated_runtime_mode.py` -> ADR 0022
  - `test_runtime_data_residency.py` -> ADR 0026
  - `test_runtime_access_control.py` -> ADR 0027
  - `test_runtime_tenant_observability.py` -> ADR 0024
- **Gap:** Não há testes de integração para o fluxo completo de Rollback em ambiente simulando produção (ex: via docker-compose em CI).

---

## 11. Registry

- **Estrutura:** Filesystem-based (`registry/tenants/{tenant}/bundles/{id}`).
- **Invariantes:** Bundles imutáveis. Aliases via JSON em `registry/control_plane/tenant_aliases.json`.
- **Código:** `validator.py` e `promoter.py` respeitam essa estrutura.

---

## 12. Gaps e Recomendações

### P0 (Bloqueador)
- **Achado:** Drift entre Schemas e Código de Validação.
- **Recomendação:** Implementar validador baseado em `jsonschema` ou `pydantic` que consuma diretamente os arquivos YAML em `contracts/`.

### P1 (Alto)
- **Achado:** Inconsistência no Relatório de Auditoria Stage 3.
- **Recomendação:** Atualizar `STAGE_3_READINESS_AUDIT.md` para refletir a existência dos dashboards e o status Accepted das ADRs.
- **Achado:** Métricas de tenant ausentes em modo compartilhado.
- **Recomendação:** Habilitar `record_tenant_request` para modo compartilhado (com cuidado com cardinalidade).

### P2/P3 (Médio/Baixo)
- **Achado:** Duplicação de Executive Overview.
- **Recomendação:** Unificar documentos em `docs/EXECUTIVE/` com versões em múltiplos idiomas se necessário.
- **Achado:** Retenção configurável.
- **Recomendação:** Evoluir `retention.yaml` para suportar overrides por `tenant_id`.

---

## APPENDIX: DRIFT CHECK

**Comparação:** `app/**` vs `build/lib/**` (simulado via `pyproject.toml` discovery).

*Nota: O diretório `build/` não está presente no ambiente atual. No entanto, o `pyproject.toml` define a inclusão de `app*` como pacote. Não foram encontrados outros pacotes ou fontes duplicadas que sugiram drift técnico.*

---
