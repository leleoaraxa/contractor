# 📘 ADR 0006 — **Multi-Tenant Observability Model**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0006 — Multi-Tenant Observability Model**

## Context

CONTRACTOR é uma plataforma multi-tenant. Observabilidade (logs, métricas, traces) é crítica para:

* diagnóstico operacional
* qualidade de respostas
* auditoria
* SLAs por tenant
* isolamento e segurança

Entretanto, observabilidade multi-tenant traz riscos conhecidos:

* explosão de cardinalidade (labels)
* vazamento de dados entre tenants
* custo elevado de métricas e logs
* dificuldade de debugging em pool compartilhado

## Decision

Adotar um **modelo de observabilidade multi-tenant controlado**, com **tenant awareness explícita**, mas **restrições rígidas de cardinalidade e exposição**.

### Princípios adotados

1. **Tenant-aware, not tenant-explosive**
2. **Observability ≠ Raw Data Visibility**
3. **Separation between Runtime Signals and Governance Signals**

## Model

### Metrics

* Todas as métricas do runtime incluem:

  * `tenant_ref` (hash ou alias estável, nunca o tenant_id bruto)
  * `bundle_id` (opcional, apenas em métricas de debug)
* Métricas globais **não** incluem tenant label.
* Cardinalidade máxima por métrica deve ser definida e validada.

Exemplos permitidos:

* `ask_latency_seconds{tenant_ref}`
* `ask_error_total{tenant_ref, error_class}`

Exemplos proibidos:

* métricas com `question`, `entity_name`, `sql_text`

### Logs

* Logs sempre passam por camada de **redaction obrigatória**.
* Logs são classificados:

  * `platform` (infra, erros genéricos)
  * `tenant-scoped` (sem payloads sensíveis)
* Logs **não** armazenam:

  * SQL completo com valores
  * dados retornados de entidades privadas

### Tracing

* Trace inclui:

  * `tenant_ref`
  * `bundle_id`
  * `request_id`
* Payloads sensíveis nunca entram no trace.
* Sampling configurável por tenant (policy-driven).

## Alternatives Considered

### 1) Full tenant labeling everywhere

**Cons:** cardinalidade explosiva, custo alto, risco operacional.

### 2) No tenant labeling

**Cons:** inviável para debug, SLAs e cobrança.

### 3) **Controlled tenant-aware model (chosen)**

**Pros:** equilíbrio entre visibilidade e custo.

## Implications

* Implementar utilitário central de métricas (`observability/metrics.py`)
* Criar política de observabilidade configurável por tenant
* Dashboards devem trabalhar com:

  * agregações
  * filtros controlados
* Debug profundo exige ativação explícita (time-boxed)

## Consequences

Observabilidade passa a ser **um contrato**, não um efeito colateral.
Isso reduz custo, risco e aumenta previsibilidade operacional.

---

