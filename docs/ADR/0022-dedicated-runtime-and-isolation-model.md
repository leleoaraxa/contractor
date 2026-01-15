# 📘 ADR 0022 — **Dedicated Runtime & Isolation Model**

**Status:** Accepted  
**Date:** 2026-01-13  
**Stage:** 3 — Enterprise Ready  
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0023 — Enterprise SLA Model
* ADR 0024 — Tenant-Level Observability

---

## Rationale

Esta ADR é ratificada porque o runtime já suporta **modo dedicado com escopo explícito por tenant** e validação de mismatch, e existe evidência documentada de isolamento de recursos no baseline de compose. Essas bases permitem formalizar o modelo Stage 3 sem extrapolar além do que está implementado.

---

## Scope (Stage 3 — Explicit)

* Runtime dedicado **opt-in por tenant**, com escopo de execução restrito ao `tenant_id` configurado.
* Mesma API do runtime compartilhado (sem divergência de contrato).
* Isolamento operacional no runtime dedicado:
  * execução do `/api/v1/runtime/ask`
  * cache dedicado por runtime
  * limites de CPU/memória no baseline compose
* Control Plane e registry de bundles permanecem **compartilhados**.

---

## Decision

Adotar o **Dedicated Runtime Model** para tenants enterprise no Stage 3, preservando:

* bundles imutáveis e aliases (`draft / candidate / current`)
* determinismo operacional
* rollback como troca de alias

---

## Isolation Boundaries

* **Incluído:** execução, cache runtime, workers e limites de recursos do runtime dedicado.
* **Excluído:** Control Plane, registry, artefatos imutáveis, e qualquer automação de provisionamento.

---

## Explicit Non-Goals

Este ADR **não define** no Stage 3:

* automação de provisionamento (containers/VMs/cluster)
* roteamento multi-região ou active-active
* política de billing por runtime dedicado
* autoscaling ou orquestração avançada

---

## Evidence / References

* `docs/EVIDENCE/stage_3/runtime_resource_isolation.md`
* `tests/integration/test_dedicated_runtime_mode.py`
* `tests/integration/test_runtime_identity_contract.py`
* `docs/EVIDENCE/stage_3/stage_3_readiness_closure.md`

---

## No Forward Commitment

“Esta ADR não constitui compromisso de implementação futura além do Stage 3.”
