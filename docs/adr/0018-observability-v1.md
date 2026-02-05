# ADR 0018 — Observabilidade v1 (métricas mínimas, tracing e logs estruturados)

**Status:** Draft
**Data:** 2026-02-XX
**Decide:** Contrato mínimo de observabilidade para Control Plane e Runtime
**Relacionados:** ADR 0004, ADR 0006, ADR 0007, ADR 0010, ADR 0014

---

## Contexto

O ADR 0004 exige sinais operacionais e auditoria mínima. Com chamadas entre Runtime e Control Plane (ADR 0010), é necessário definir o conjunto mínimo de métricas, logs estruturados e tracing para suportar operação e incidentes.

---

## Decisão a ser tomada

Definir:
- métricas mínimas (v1),
- tracing mínimo (propagação e atributos),
- logging estruturado mínimo,
- SLOs mínimos (se aplicável) e alertas (se aplicável).

---

## Fora de escopo

- dashboards completos e runbooks detalhados

---

## Próximos passos

Definir e promover este ADR antes de declarar prontidão operacional.
