# Evidência — Observabilidade Enterprise Mínima (Stage 3)

**Objetivo:** documentar a observabilidade mínima exigida no Stage 3 (Enterprise Ready) para auditoria do item 2 (Observability) do ADR 0028, **sem** avançar para Stage 4.

**Escopo:** somente métricas já existentes (`runtime_tenant_*`, `contractor:*`), logs estruturados sem payload, e evidências documentais/runbooks. Nenhum dashboard versionado foi criado neste artefato.

## Tabela de evidências (ADR 0028 → Observability 2.1–2.5)

| Item (ADR 0028) | Evidência concreta | Status | Limitações explícitas |
| --- | --- | --- | --- |
| **2.1 Métricas segregadas por tenant** | `tests/integration/test_runtime_tenant_observability.py` valida o label `tenant_ref` na métrica `runtime_tenant_http_requests_total`. | **PASS** | Evidência baseada em teste de integração; não cria métricas novas. |
| **2.2 Dashboards dedicados por tenant** | Não há dashboards versionados em `ops/` ou `docs/`. | **FAIL** | Dashboards por tenant **ainda não versionados**; métricas existentes permitem criação futura sem refatoração. |
| **2.3 Logs sem payload sensível** | ADR 0018 define telemetria como **logs redigidos** e ausência de payload; `docs/RUNBOOKS/privacy_retention.md` orienta evitar logging de payload. | **FAIL** | Não há teste automatizado ou evidência operacional que comprove logs estruturados sem payload em runtime dedicado; evidência atual é normativa (política), não comprobatória. |
| **2.4 Retenção configurável por tenant/plano** | `ops/observability/retention.yaml` documenta defaults globais de retenção. | **FAIL** | Não existe override por tenant/plano documentado ou aplicado; somente defaults globais. |
| **2.5 Modelo documentado (ADR 0024)** | `docs/ADR/0024-tenant-level-observability.md` define métricas, logs, traces e princípios por tenant. | **PASS** | ADR 0024 aprovado; itens 2.2–2.4 permanecem **FAIL** por ausência de implementação/evidência. |

## Notas de auditoria (sem ambiguidade)

- **Nenhuma métrica nova foi criada** nesta evidência; apenas referências a métricas já existentes (`runtime_tenant_*`, `contractor:*`).
- **Dashboards por tenant não estão versionados** e permanecem como gap legítimo para Stage 3.
- **Logs sem payload sensível** estão documentados como política (ADR 0018 + runbook), porém **não há prova automática ou operacional** de enforcement no runtime.
- **Retenção por tenant/plano** não está implementada; há somente defaults globais em `ops/observability/retention.yaml`.

## Stage 3 — Trilha C (Observability): CONCLUÍDA

**Status global:** Trilha C = **DONE**.

**Checklist Trilha C (C1 → C5)**

| Item | Status | Evidência/nota curta |
| --- | --- | --- |
| **C1** — Instrumentação HTTP do runtime (`http_requests_total`) | **DONE** | Métrica exposta no runtime com labels de serviço/método/path/status. |
| **C2** — Labels de tenant nas métricas do runtime | **DONE** | Teste de integração valida `runtime_tenant_http_requests_total` com `tenant_ref`. |
| **C3** — Endpoint `/metrics` disponível no runtime | **DONE** | Evidência operacional local via `curl` no runtime. |
| **C4** — Teste de integração de observabilidade do runtime | **DONE** | `tests/integration/test_runtime_tenant_observability.py`. |
| **C5** — Hardening de cardinalidade em métricas HTTP | **DONE** | Alta cardinalidade em métricas HTTP mitigada via route template (sem mudança de contrato). |

**Notas obrigatórias (Trilha C):**

- **Não há registry custom** (usa registry padrão do `prometheus_client`).
- **Contrato de métricas preservado com extensão compatível:** labels existentes permanecem (`tenant_id`) e foi **adicionado** `tenant_ref` para uso em dashboards.
- **Hash de `tenant_ref` é determinístico/estável**, mas **não é anonimização forte** (não há segredo; reversível por brute-force de baixa entropia).
- **Mitigação de cardinalidade via route template** (`path` expõe `/api/v1/runtime/ask/result/{request_id}`).
- **Referência ADR:** ADR 0024 — Tenant-Level Observability.

### Evidências

#### (a) Evidência de cardinalidade mitigada

**Comandos executados (runtime local):**

```bash
curl -s -o /dev/null -w "%{http_code}\n" -H 'X-API-Key: dev-key' \
  http://localhost:8000/api/v1/runtime/ask/result/123e4567-e89b-12d3-a456-426614174000
curl -s -o /dev/null -w "%{http_code}\n" -H 'X-API-Key: dev-key' \
  http://localhost:8000/api/v1/runtime/ask/result/123e4567-e89b-12d3-a456-426614174000/raw
curl -s http://localhost:8000/metrics | rg "http_requests_total\\{"
```

**Antes (path dinâmico com `request_id` em rota não roteada, sem template):**

```
http_requests_total{method="GET",path="/api/v1/runtime/ask/result/123e4567-e89b-12d3-a456-426614174000/raw",service="runtime",status_code="404"} 1.0
```

**Depois (path com template `{request_id}`):**

```
http_requests_total{method="GET",path="/api/v1/runtime/ask/result/{request_id}",service="runtime",status_code="503"} 1.0
```

#### (b) Evidência de teste automatizado

- **Teste de integração:** `test_http_metrics_use_route_template_for_dynamic_paths`.
- **Comando executado:**

```bash
pytest -q tests/integration/test_runtime_tenant_observability.py -k "http_metrics_use_route_template_for_dynamic_paths"
```

- **Resultado:**

```
1 passed, 2 deselected in 0.85s
```

#### (c) Evidência operacional local (compose)

> **Nota factual:** o ambiente atual não possui `docker`/`docker-compose`. A evidência abaixo foi obtida com o runtime local (equivalente ao serviço `runtime` do compose), mantendo os mesmos endpoints.

**Curl real ao endpoint `/metrics` do runtime:**

```bash
curl -s http://localhost:8000/metrics | rg "http_requests_total\\{"
```

**Confirmação:** o label `path` expõe o template `/api/v1/runtime/ask/result/{request_id}` e **não** contém o valor literal de `request_id`.

## Referências

- ADR 0024 — Tenant-Level Observability.
- ADR 0028 — Stage 3 Completion & Readiness Checklist.
- ADR 0018 — Data Privacy, LGPD/GDPR and Retention Policies.
- Runbook vigente/base — Privacidade e retenção.
- Teste de integração — `tests/integration/test_runtime_tenant_observability.py`.
