# 📘 ADR 0024 — **Tenant-Level Observability**

**Status:** Draft
**Date:** 2026-01-13
**Stage:** 3 — Enterprise Ready
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0022 — Dedicated Runtime & Isolation Model
* ADR 0023 — Enterprise SLA Model
* ADR 0018 — Data Privacy, LGPD/GDPR and Retention Policies

---

## Context

Com a introdução de **runtimes dedicados por tenant** (ADR 0022) e **SLAs contratuais** (ADR 0023), a plataforma CONTRACTOR passa a ter a obrigação de fornecer **observabilidade isolada, mensurável e auditável** por tenant.

No Stage 2, a observabilidade é:

* majoritariamente global
* focada em operação interna
* suficiente para SLOs, mas **insuficiente para SLA enterprise**

Clientes enterprise exigem:

* visibilidade clara do **seu** runtime
* evidências objetivas de SLA
* dados observáveis **sem vazamento cross-tenant**
* linguagem operacional compreensível (não debug interno)

---

## Decision

Adotar um **modelo de Tenant-Level Observability**, no qual cada tenant Stage 3 possui:

* métricas isoladas
* logs segregados
* traces escopados
* relatórios alinhados a SLA

A observabilidade por tenant é **obrigatória para Stage 3** e **indisponível em runtime compartilhado**.

---

## Observability Principles

1. **Isolation first**
2. **Observability is evidence, not debugging**
3. **SLA drives metrics**
4. **No payload leakage**
5. **Least necessary visibility**

---

## Scope of Observability (Stage 3)

### 1. Covered Components

Observabilidade por tenant cobre exclusivamente:

* **Runtime dedicado**

  * execução do `/api/v1/runtime/ask`
* pipelines internos do runtime
* dependências diretas do runtime (ex.: cache, worker interno)

O **Control Plane** não expõe observabilidade detalhada por tenant no Stage 3.

---

## Metrics Model

### 2. Tenant-Level Metrics

Métricas **obrigatórias** por tenant:

| Categoria    | Métrica                         |
| ------------ | ------------------------------- |
| Availability | taxa de sucesso (2xx / total)   |
| Latency      | p50, p95                        |
| Error Rate   | 4xx, 5xx                        |
| Throughput   | requests/min                    |
| Saturation   | filas, workers, uso de recursos |

Todas as métricas devem ser:

* agregadas
* rotuladas por `tenant_id`
* coletadas **apenas** no runtime dedicado

---

## Logging Model

### 3. Tenant-Isolated Logs

Logs por tenant devem:

* ser segregados por runtime
* conter apenas:

  * request_id
  * timestamps
  * status
  * identifiers técnicos
* **nunca** conter:

  * payload (`question`)
  * dados de domínio
  * credenciais

Logs detalhados são **internos** e não expostos ao tenant.

---

## Tracing Model

### 4. Scoped Tracing

* Traces são:

  * opcionais no Stage 3
  * habilitados por tenant
* Traces:

  * não cruzam tenants
  * não carregam payload sensível
  * focam em latência e dependências

---

## SLA Evidence & Reporting

### 5. SLA-Aligned Reports

Para tenants com SLA ativo:

* relatório mensal por tenant contendo:

  * disponibilidade
  * latência
  * incidentes relevantes
* dados:

  * derivados das métricas de observabilidade
  * imutáveis após fechamento do período

O relatório é a **fonte oficial de SLA evidence**.

---

## Access Model

### 6. Who Can See What

| Papel               | Acesso                          |
| ------------------- | ------------------------------- |
| Tenant              | métricas agregadas + relatórios |
| Operação CONTRACTOR | observabilidade completa        |
| Engenharia          | logs/traces internos            |
| Comercial           | relatórios de SLA               |

---

## Privacy & Compliance

* Total alinhamento com **ADR 0018**
* CONTRACTOR atua como **Data Processor**
* Observabilidade:

  * não classifica PII
  * não armazena dados de domínio
  * respeita retenção por policy

---

## Retention

* Métricas: conforme policy do tenant (default enterprise)
* Logs: retenção curta, configurável
* Traces: curta duração, opt-in

Nenhum dado observável tem retenção infinita.

---

## Incident Management Integration

* Alertas por tenant alimentam:

  * incidentes SEV-1 / SEV-2
* Postmortems:

  * referenciam métricas tenant-level
  * alimentam relatórios de SLA

---

## Alternatives Considered

### 1) Observabilidade global apenas

**Cons:** viola isolamento enterprise.

---

### 2) Observabilidade raw por tenant

**Cons:** risco de vazamento e PII.

---

### 3) **Tenant-level aggregated observability (chosen)**

**Pros:**

* segura
* auditável
* alinhada a SLA
* escalável

---

## Consequences

* O produto passa a:

  * vender **transparência controlada**
  * reduzir disputas contratuais
* A engenharia ganha:

  * métricas claras
  * menos debugging reativo
* O comercial ganha:

  * evidência concreta de valor

---

## Explicit Non-Goals

Este ADR **não define**:

* dashboards customizados por cliente
* acesso direto a Prometheus/Grafana
* tracing distribuído cross-service
* analytics avançado de uso

Esses itens pertencem ao Stage 4.

---

## Final Notes

Sem observabilidade por tenant, **não existe SLA real**.

Este ADR fecha o **núcleo operacional do Stage 3**:

* isolamento (ADR 0022)
* SLA (ADR 0023)
* evidência (ADR 0024)

---
