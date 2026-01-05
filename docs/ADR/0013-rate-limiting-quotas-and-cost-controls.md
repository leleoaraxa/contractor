# 📘 ADR 0013 — **Rate Limiting, Quotas and Cost Controls**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0013 — Rate Limiting, Quotas and Cost Controls**

## Context

CONTRACTOR executa:

* queries potencialmente custosas
* chamadas a LLMs
* operações multi-tenant em pool compartilhado

Sem limites explícitos, um tenant pode:

* degradar o serviço de outros
* gerar custos imprevisíveis
* causar incidentes operacionais

É necessário controlar **uso, custo e fairness** desde o MVP.

## Decision

Adotar um modelo **policy-driven de rate limiting, quotas e controle de custo**, aplicado por tenant e por tipo de recurso.

### Princípios

1. **Noisy tenant isolation**
2. **Cost visibility before cost optimization**
3. **Limits are contractual**

## Model

### Rate Limiting

* Aplicado no runtime e gateway
* Escopos:

  * por tenant
  * por endpoint (/ask, quality runs, etc.)
* Implementação inicial:

  * token bucket ou leaky bucket
  * Redis-backed
* Políticas declaradas no bundle ou plano do tenant

### Quotas

* Definidas por período (ex.: diário, mensal):

  * número de requests
  * tempo total de execução SQL
  * tokens LLM
* Quotas são **hard limits** no MVP (sem overage automático).

### Cost Controls

* Runtime registra métricas de custo estimado:

  * tempo de DB
  * volume de dados
  * tokens LLM
* Control Plane agrega e expõe relatórios por tenant.
* Alertas configuráveis:

  * 70%, 90%, 100% da quota

## Enforcement

* Ao exceder limites:

  * requisição é rejeitada com erro explícito e rastreável
  * nenhum fallback silencioso
* Limites diferenciáveis por plano (Starter / Pro / Enterprise).

## Alternatives Considered

### 1) Sem limites no MVP

**Cons:** risco financeiro e operacional grave.

### 2) Limites globais apenas

**Cons:** injustiça entre tenants.

### 3) **Policy-driven per-tenant limits (chosen)**

**Pros:** previsibilidade, escalabilidade comercial.

## Implications

* Control Plane deve:

  * gerenciar planos e limites
  * expor uso e consumo
* Runtime deve:

  * aplicar limites antes da execução pesada
  * registrar métricas de consumo
* Dashboards e alertas são parte do produto, não extras.

## Consequences

O custo passa a ser **mensurável, controlável e comunicável**, viabilizando escala sustentável e contratos enterprise.

---
