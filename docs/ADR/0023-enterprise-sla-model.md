# 📘 ADR 0023 — **Enterprise SLA Model**

**Status:** Accepted  
**Date:** 2026-01-13  
**Stage:** 3 — Enterprise Ready  
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0022 — Dedicated Runtime & Isolation Model
* ADR 0024 — Tenant-Level Observability

---

## Rationale

Esta ADR é ratificada para formalizar o **modelo de SLA Stage 3** com base em métricas já expostas e evidências de observabilidade por tenant, sem assumir contratos ou penalidades que ainda não existem no repositório. A aceitação serve para alinhar governança e limites do que é mensurável hoje.

---

## Scope (Stage 3 — Explicit)

* SLA **aplicável somente ao runtime dedicado** (`/api/v1/runtime/ask`).
* Métricas derivadas de telemetria existente (disponibilidade e latência agregada).
* Relatórios e apuração baseados em observabilidade tenant-level quando configurada.
* O Control Plane **não** está coberto por SLA no Stage 3.

---

## Decision

Adotar um **Enterprise SLA Model** baseado em:

* SLOs mensuráveis e auditáveis
* isolamento por tenant (runtime dedicado)
* escopo restrito ao runtime

---

## Measurement Model (Stage 3)

* **Disponibilidade:** sucesso de requests 2xx/total para `/api/v1/runtime/ask`.
* **Latência agregada:** percentis (p50/p95) calculados a partir das métricas do runtime.
* **Janela de apuração:** mensal, com fechamento imutável do período.

> Targets contratuais específicos **não são definidos** no repositório no Stage 3.

---

## Explicit Non-Goals

Este ADR **não define** no Stage 3:

* targets de SLA contratuais específicos
* modelo de créditos/penalidades formal
* SLA para Control Plane, billing ou marketplace
* disaster recovery ou multi-região ativa-ativa

---

## Evidence / References

* `docs/EVIDENCE/stage_3/observability_enterprise_minimum.md`
* `docs/EVIDENCE/stage_3/stage_3_readiness_closure.md`
* `docs/RUNBOOKS/slo_active.md`
* `tests/integration/test_runtime_tenant_observability.py`

---

## No Forward Commitment

“Esta ADR não constitui compromisso de implementação futura além do Stage 3.”
