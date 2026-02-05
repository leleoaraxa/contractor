# ADR 0014 — Auditoria end-to-end (formato, correlação e retenção mínima)

**Status:** Draft
**Data:** 2026-02-XX
**Decide:** Modelo de auditoria end-to-end (Control Plane + Runtime)
**Relacionados:** ADR 0004, ADR 0006, ADR 0007, ADR 0010, ADR 0011, ADR 0012

---

## Contexto

O ADR 0004 define auditoria mínima obrigatória, mas não fixa formato, correlação entre serviços e retenção.
Com a separação Control Plane/Runtime e chamadas entre eles (ADR 0010), é necessário definir o contrato de auditoria end-to-end para suportar rastreabilidade e governança.

---

## Decisão a ser tomada

Definir:
- esquema mínimo do evento de auditoria,
- chaves de correlação (ex.: request_id/trace_id),
- retenção mínima e redaction (se aplicável),
- onde eventos são emitidos e como são consumidos.

---

## Fora de escopo

- SIEM corporativo e integrações externas específicas

---

## Próximos passos

Definir e promover este ADR antes de afirmar compliance de auditoria completa.
