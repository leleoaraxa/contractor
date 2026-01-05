# 📘 ADR 0019 — **Incident Management and SLOs**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0019 — Incident Management and SLOs**

## Context

CONTRACTOR é uma plataforma operacional crítica para clientes. Incidentes não tratados de forma estruturada geram:

* downtime prolongado
* impacto cross-tenant
* perda de confiança
* dificuldade de aprendizado organizacional

É necessário definir **como incidentes são detectados, classificados, respondidos e aprendidos**, além de SLOs claros.

## Decision

Adotar um **modelo formal de Incident Management**, com **SLOs explícitos**, **error budgets** e **postmortems obrigatórios**.

### Princípios

1. **Incidents are expected, chaos is not**
2. **Blameless postmortems**
3. **Reliability is a feature**

## Incident Model

### Incident Severity Levels

* **SEV-1**: indisponibilidade total ou vazamento de dados
* **SEV-2**: degradação significativa (latência, erros elevados)
* **SEV-3**: impacto limitado ou intermitente
* **SEV-4**: incidente operacional sem impacto ao cliente

### Response Requirements

| Severity | Acknowledge | Mitigate |
| -------- | ----------- | -------- |
| SEV-1    | ≤ 15 min    | ≤ 60 min |
| SEV-2    | ≤ 30 min    | ≤ 2 h    |
| SEV-3    | ≤ 2 h       | ≤ 1 dia  |
| SEV-4    | Best effort | Planned  |

## SLO Model

### Core SLOs (v0)

* **Availability**: 99.9% (runtime)
* **Latency (p95 /ask)**: policy-defined (ex.: ≤ 2s)
* **Error Rate**: ≤ 0.1%
* **Routing Accuracy**: conforme Quality Gates (ADR 0009)

### Error Budgets

* Cada SLO tem budget mensal.
* Esgotamento do budget:

  * congela deploys não críticos
  * prioriza confiabilidade sobre features

## Detection and Alerting

* Alertas baseados em SLOs, não em métricas brutas.
* Alertas diferenciados por ambiente.
* Alertas de segurança têm prioridade SEV-1.

## Postmortem Process

* Obrigatório para SEV-1 e SEV-2.
* Conteúdo mínimo:

  * timeline
  * impacto
  * causa raiz
  * ações corretivas
  * prevenção futura
* Postmortems são artefatos versionados (internos).

## Alternatives Considered

### 1) Resposta ad hoc

**Cons:** aprendizado nulo; repetição de falhas.

### 2) Foco apenas em uptime

**Cons:** ignora qualidade e segurança.

### 3) **SLO + Incident framework (chosen)**

**Pros:** maturidade operacional; confiança enterprise.

## Implications

* Observability deve suportar SLO computation.
* Runbooks por tipo de incidente.
* Incidentes alimentam roadmap (tech debt visível).

## Consequences

Confiabilidade passa a ser **parte explícita do produto**, não um esforço reativo.

---
