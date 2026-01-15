# 📘 ADR 0024 — **Tenant-Level Observability**

**Status:** Accepted  
**Date:** 2026-01-13  
**Stage:** 3 — Enterprise Ready  
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0022 — Dedicated Runtime & Isolation Model
* ADR 0023 — Enterprise SLA Model
* ADR 0018 — Data Privacy, LGPD/GDPR and Retention Policies

---

## Rationale

Esta ADR é ratificada porque a plataforma já expõe métricas com escopo de tenant e possui evidências documentadas de observabilidade mínima, o que permite formalizar o que é auditável no Stage 3 e declarar explicitamente os gaps remanescentes.

---

## Scope (Stage 3 — Explicit)

* Métricas agregadas por tenant no runtime dedicado.
* Logs estruturados com redaction de payload no contexto de evidências non-prod.
* Traces apenas se habilitados por tenant (não obrigatórios).
* Observabilidade limitada ao runtime; Control Plane permanece com visibilidade interna.

---

## Observability Model (Stage 3)

* **Métricas obrigatórias:** disponibilidade, latência (p50/p95), error rate e throughput por tenant.
* **Logs:** sem payload de request; somente identificadores técnicos e status.
* **Relatórios de SLA:** derivados das métricas agregadas quando aplicável.

---

## Explicit Non-Goals

Este ADR **não define** no Stage 3:

* dashboards versionados por tenant
* acesso direto do tenant a Prometheus/Grafana
* retenção configurável por tenant/plano
* tracing distribuído cross-service

---

## Evidence / References

* `docs/EVIDENCE/stage_3/observability_enterprise_minimum.md`
* `docs/EVIDENCE/stage_3/logs_no_payload_nonprod.md`
* `tests/integration/test_runtime_tenant_observability.py`
* `docs/RUNBOOKS/privacy_retention.md`

---

## No Forward Commitment

“Esta ADR não constitui compromisso de implementação futura além do Stage 3.”
