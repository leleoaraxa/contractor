# Evidência — Observability Enterprise Mínima (Stage 3)

**Objetivo:** documentar a observability mínima exigida no Stage 3 (Enterprise Ready) para auditoria do item 2 (Observability) do ADR 0028, **sem** avançar para Stage 4.

**Escopo:** somente métricas já existentes (`runtime_tenant_*`, `contractor:*`), logs estruturados sem payload, e evidências documentais/runbooks. Nenhum dashboard versionado foi criado neste artefato.

## Tabela de evidências (ADR 0028 → Observability 2.1–2.5)

| Item (ADR 0028) | Evidência concreta | Status | Limitações explícitas |
| --- | --- | --- | --- |
| **2.1 Métricas segregadas por tenant** | `tests/integration/test_runtime_tenant_observability.py` valida o label `tenant_id` na métrica `runtime_tenant_http_requests_total`. | **PASS** | Evidência baseada em teste de integração; não cria métricas novas. |
| **2.2 Dashboards dedicados por tenant** | Não há dashboards versionados em `ops/` ou `docs/`. | **FAIL** | Dashboards por tenant **ainda não versionados**; métricas existentes permitem criação futura sem refatoração. |
| **2.3 Logs sem payload sensível** | ADR 0018 define telemetria como **logs redigidos** e ausência de payload; `docs/RUNBOOKS/privacy_retention.md` orienta evitar logging de payload. | **FAIL** | Não há teste automatizado ou evidência operacional que comprove logs estruturados sem payload em runtime dedicado; evidência atual é normativa (política), não comprobatória. |
| **2.4 Retenção configurável por tenant/plano** | `ops/observability/retention.yaml` documenta defaults globais de retenção. | **FAIL** | Não existe override por tenant/plano documentado ou aplicado; somente defaults globais. |
| **2.5 Modelo documentado (ADR 0024)** | `docs/ADR/0024-tenant-level-observability.md` define métricas, logs, traces e princípios por tenant. | **PASS** | Documento está em status Draft; requer aprovação formal para fechamento de Stage 3. |

## Notas de auditoria (sem ambiguidade)

- **Nenhuma métrica nova foi criada** nesta evidência; apenas referências a métricas já existentes (`runtime_tenant_*`, `contractor:*`).
- **Dashboards por tenant não estão versionados** e permanecem como gap legítimo para Stage 3.
- **Logs sem payload sensível** estão documentados como política (ADR 0018 + runbook), porém **não há prova automática ou operacional** de enforcement no runtime.
- **Retenção por tenant/plano** não está implementada; há somente defaults globais em `ops/observability/retention.yaml`.

## Referências

- ADR 0024 — Tenant-Level Observability.
- ADR 0028 — Stage 3 Completion & Readiness Checklist.
- ADR 0018 — Data Privacy, LGPD/GDPR and Retention Policies.
- Runbook — Privacidade e retenção (Stage 2).
- Teste de integração — `tests/integration/test_runtime_tenant_observability.py`.
