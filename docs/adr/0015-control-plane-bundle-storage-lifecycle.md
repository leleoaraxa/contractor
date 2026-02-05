# ADR 0015 — Armazenamento de bundles no Control Plane (integridade e lifecycle)

**Status:** Draft
**Data:** 2026-02-XX
**Decide:** Storage v1 de bundles imutáveis e lifecycle (GC)
**Relacionados:** ADR 0002, ADR 0005, ADR 0006

---

## Contexto

Os ADRs 0002 e 0005 exigem bundles imutáveis e modelo mínimo de bundle. Para materializar governança real,
o Control Plane precisa definir onde bundles são armazenados, como integridade é garantida (ex.: digest), e como lifecycle/GC funciona.

---

## Decisão a ser tomada

Definir:
- backend de storage v1,
- como digest/imutabilidade são verificados,
- políticas mínimas de retenção e garbage collection,
- interfaces mínimas necessárias na API do Control Plane.

---

## Fora de escopo

- replicação multi-região
- deduplicação avançada

---

## Próximos passos

Definir e promover este ADR antes de implementar publish real com armazenamento persistente.
