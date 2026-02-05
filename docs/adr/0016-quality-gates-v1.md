# ADR 0016 — Quality gates v1 (suites, execução e critérios de promoção)

**Status:** Draft
**Data:** 2026-02-XX
**Decide:** Quality gates v1 para promoção de bundles
**Relacionados:** ADR 0005, ADR 0006, ADR 0009, ADR 0019

---

## Contexto

O caso de uso demo (ADR 0009) utiliza suites/golden em testes, mas não há um contrato governado de quality gate no Control Plane para permitir promoção de bundles de forma auditável e determinística.

---

## Decisão a ser tomada

Definir:
- tipos de suites suportadas (v1),
- como execução ocorre e onde (Control Plane),
- critérios mínimos de aprovação,
- como resultados impactam promoção/rollback (ver ADR 0019).

---

## Fora de escopo

- métricas avançadas e ranking de qualidade

---

## Próximos passos

Definir e promover este ADR antes de afirmar “promoção governada por gates”.
