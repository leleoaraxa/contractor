# 📘 ADR 0025 — **Enterprise Incident & Escalation Model**

**Status:** Accepted  
**Date:** 2026-01-13  
**Stage:** 3 — Enterprise Ready  
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0022 — Dedicated Runtime & Isolation Model
* ADR 0023 — Enterprise SLA Model
* ADR 0024 — Tenant-Level Observability
* ADR 0018 — Data Privacy, LGPD/GDPR and Retention Policies

---

## Rationale

Esta ADR é ratificada para alinhar o tratamento de incidentes Stage 3 ao que já está documentado em runbooks e evidências, explicitando a integração com observabilidade e SLA sem introduzir tooling ou compromissos não implementados.

---

## Scope (Stage 3 — Explicit)

* Incidentes definidos a partir de degradação mensurável no runtime dedicado.
* Escalonamento e comunicação baseados em runbooks existentes.
* Integração documental com rollback e postmortem.
* Severidades formalmente documentadas no Stage 3 seguem o que os runbooks cobrem hoje.

---

## Incident Model (Stage 3)

* **SEV-1 a SEV-3** são definidos e operados via runbook.
* **SEV-4** permanece como lacuna declarada (não documentado nos runbooks atuais).
* Incidentes afetam apuração de SLA quando aplicável.

---

## Explicit Non-Goals

Este ADR **não define** no Stage 3:

* suporte 24x7 global ou NOC dedicado
* ferramentas de pager/escalation externas (PagerDuty/Opsgenie)
* processos regulatórios formais (SOC2/ISO)
* automação de DR multi-região

---

## Evidence / References

* `docs/RUNBOOKS/incident_management.md`
* `docs/incidents/_template.md`
* `docs/RUNBOOKS/rollback.md`
* `docs/EVIDENCE/stage_3/stage_3_readiness_closure.md`

---

## No Forward Commitment

“Esta ADR não constitui compromisso de implementação futura além do Stage 3.”
