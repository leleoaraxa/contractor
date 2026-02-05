# ADR 0017 — Distribuição de bundles para o Runtime (fetch, digest e cache local)

**Status:** Draft
**Data:** 2026-02-XX
**Decide:** Como o Runtime obtém bundles imutáveis promovidos
**Relacionados:** ADR 0002, ADR 0005, ADR 0007, ADR 0010, ADR 0015

---

## Contexto

O Runtime resolve `current` via Control Plane e recebe `bundle_id` (ADR 0010). Ainda falta definir como o Runtime obtém o bundle correspondente (fetch), como verifica integridade/imutabilidade (digest) e como cache local funciona sem quebrar governança.

---

## Decisão a ser tomada

Definir:
- mecanismo v1 de fetch,
- verificação de digest,
- cache local (TTL/eviction) e comportamento fail-closed,
- como isso se integra ao Control Plane (endpoints/contratos).

---

## Fora de escopo

- CDN global e otimizações avançadas

---

## Próximos passos

Definir e promover este ADR antes de trocar “bundle path local” por distribuição governada real.
