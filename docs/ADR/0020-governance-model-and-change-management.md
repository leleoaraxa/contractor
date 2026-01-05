# 📘 ADR 0020 — **Governance Model and Change Management**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0020 — Governance Model and Change Management**

## Context

CONTRACTOR é uma plataforma multi-tenant, orientada a contratos, com múltiplos stakeholders:

* time de plataforma
* times de clientes (técnicos e não técnicos)
* parceiros e integradores
* clientes enterprise com requisitos formais

Sem um modelo explícito de governança e gestão de mudanças, a plataforma corre riscos de:

* decisões inconsistentes
* quebra de contratos
* deriva arquitetural
* retrabalho recorrente
* perda de previsibilidade para clientes

É necessário estabelecer **quem decide o quê**, **como mudanças são propostas**, **como são aprovadas** e **como são comunicadas**.

## Decision

Adotar um **Governance Model explícito**, baseado em:

* **ADRs como fonte de verdade decisória**
* **políticas versionadas como mecanismo operacional**
* **processo formal de change management**, proporcional ao impacto

### Princípios

1. **Decisions are documented, not implicit**
2. **Governance scales with impact**
3. **Change is controlled, not blocked**

## Governance Structure

### Decision Domains

* **Platform Architecture**

  * decisões estruturais (pipeline, isolamento, segurança, observability)
  * requer ADR
* **Product & Commercial**

  * planos, limites, features
  * documentado via policies + roadmap
* **Tenant Configuration**

  * contratos, bundles, policies por tenant
  * governado via Control Plane
* **Operational**

  * incidentes, SLOs, deploys
  * governado por runbooks e SRE practices

### Decision Authority

* **Platform Core Team**

  * aprova ADRs
  * define padrões globais
* **Tenant Admins**

  * gerenciam contratos e bundles do próprio tenant
* **Operators / SRE**

  * podem bloquear releases por risco operacional

## Change Management Process

### Change Classification

* **Low Impact**

  * ajustes internos
  * melhorias não-breaking
  * não exige ADR
* **Medium Impact**

  * novas features
  * novas policies
  * exige design note ou mini-ADR
* **High Impact**

  * breaking changes
  * mudanças de segurança, privacidade ou isolamento
  * **ADR obrigatório**

### Change Flow

1. Proposal (ADR / design doc)
2. Review (core team)
3. Decision (accept / reject / defer)
4. Communication (changelog, docs)
5. Implementation
6. Validation (quality gates)
7. Release

## Communication and Transparency

* ADRs são públicos internamente e versionados.
* Changelog por versão major/minor.
* Deprecations comunicadas com antecedência contratual.

## Alternatives Considered

### 1) Governança informal

**Cons:** inconsistência, decisões perdidas, retrabalho.

### 2) Governança pesada (comitês rígidos)

**Cons:** lentidão, atrito, inovação travada.

### 3) **ADR-driven governance (chosen)**

**Pros:** clareza, histórico, escalabilidade organizacional.

## Implications

* Todo desenvolvedor deve conhecer e respeitar ADRs.
* Revisões arquiteturais são parte do fluxo normal.
* ADRs rejeitados permanecem como registro histórico.

## Consequences

A governança deixa de ser tácita e passa a ser **explícita, auditável e evolutiva**, reduzindo risco técnico e organizacional.

---
