# ADR 0019 — Promoção e rollback v1 (workflow de aliases e invariantes)

**Status:** Draft
**Data:** 2026-02-XX
**Decide:** Workflow v1 de promoção/rollback usando aliases (`draft`, `candidate`, `current`)
**Relacionados:** ADR 0003, ADR 0004, ADR 0006, ADR 0016

---

## Contexto

O ADR 0003 define aliases por tenant (`draft`, `candidate`, `current`) para promoção e rollback, mas ainda não há workflow formalizado com invariantes operacionais, nem contrato de como o Control Plane aplica mudanças com auditoria.

---

## Decisão a ser tomada

Definir:
- estados e transições permitidas entre aliases (v1),
- invariantes (ex.: `current` só muda via gate aprovado),
- rollback explícito e auditado,
- efeitos colaterais esperados (ex.: invalidar cache, etc.) sem assumir implementação específica.

---

## Fora de escopo

- automação de rollback
- múltiplos runtimes/ambientes

---

## Próximos passos

Definir e promover este ADR antes de materializar endpoints de promote/rollback do Control Plane.
