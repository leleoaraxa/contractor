# 📘 ADR 0026 — **Enterprise Data Residency & Compliance Boundaries**

**Status:** Accepted  
**Date:** 2026-01-13  
**Stage:** 3 — Enterprise Ready  
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0022 — Dedicated Runtime & Isolation Model
* ADR 0023 — Enterprise SLA Model
* ADR 0024 — Tenant-Level Observability
* ADR 0025 — Enterprise Incident & Escalation Model
* ADR 0018 — Data Privacy, LGPD/GDPR and Retention Policies

---

## Rationale

Esta ADR é ratificada porque o runtime já expõe metadados de residency e aplica verificação de região em modo dedicado, permitindo definir limites claros de compliance sem prometer controle sobre processamento efêmero ou infraestrutura externa.

---

## Scope (Stage 3 — Explicit)

* Residency aplicada **somente a dados persistidos** (metadata, logs, métricas).
* Runtime dedicado expõe região configurada e valida requisitos de residency quando configurados.
* Responsabilidades de Data Processor/Data Controller seguem ADR 0018.

---

## Boundaries (Stage 3)

* **Garantido:** residência de dados persistidos no escopo configurado.
* **Não garantido:** processamento in-memory estritamente regional, tráfego de backbone do provedor, ou isolamento físico dedicado.

---

## Explicit Non-Goals

Este ADR **não define** no Stage 3:

* sovereign cloud ou ambientes air-gapped
* certificações regulatórias formais (SOC2/ISO)
* multi-region active-active
* zero cross-region network traffic

---

## Evidence / References

* `tests/integration/test_runtime_data_residency.py`
* `docs/RUNBOOKS/privacy_retention.md`
* `docs/EVIDENCE/stage_3/stage_3_readiness_closure.md`

---

## No Forward Commitment

“Esta ADR não constitui compromisso de implementação futura além do Stage 3.”
