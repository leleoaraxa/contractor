# 📘 ADR 0027 — **Enterprise Access Control & Identity Boundaries**

**Status:** Accepted  
**Date:** 2026-01-13  
**Stage:** 3 — Enterprise Ready  
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0022 — Dedicated Runtime & Isolation Model
* ADR 0023 — Enterprise SLA Model
* ADR 0024 — Tenant-Level Observability
* ADR 0025 — Enterprise Incident & Escalation Model
* ADR 0026 — Enterprise Data Residency & Compliance Boundaries
* ADR 0018 — Data Privacy, LGPD/GDPR and Retention Policies

---

## Rationale

Esta ADR é ratificada porque o runtime já aplica **chaves com escopo por tenant e role**, e há evidência operacional non-prod de rotação/revogação de credenciais e auditoria. Isso permite formalizar fronteiras de identidade no Stage 3 sem introduzir IAM externo.

---

## Scope (Stage 3 — Explicit)

* Autenticação por API keys com escopo `<tenant_id>:<role>`.
* Rejeição de chaves sem escopo ou com role inadequada no runtime.
* Rotação/revogação manual via configuração e restart controlado.
* Audit log de ações sensíveis no Control Plane.

---

## Access Control Model (Stage 3)

* Roles suportados no runtime: **tenant_runtime_client** (execução de `/ask`).
* Operação e auditoria documentadas por runbooks existentes.
* Identidades sempre associadas a um único tenant.

---

## Explicit Non-Goals

Este ADR **não define** no Stage 3:

* IAM granular dinâmico (ABAC)
* federação obrigatória de identidade (SSO/IdP)
* MFA obrigatório
* gestão automática de usuários finais

---

## Evidence / References

* `tests/integration/test_runtime_access_control.py`
* `tests/integration/test_runtime_identity_contract.py`
* `docs/EVIDENCE/stage_3/credential_rotation_nonprod.md`
* `docs/EVIDENCE/stage_3/audit_actions_nonprod.md`
* `docs/EVIDENCE/stage_3/logs_no_payload_nonprod.md`

---

## No Forward Commitment

“Esta ADR não constitui compromisso de implementação futura além do Stage 3.”
