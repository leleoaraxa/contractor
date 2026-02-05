# ADR 0013 — Rate limiting e quotas (policy-driven)

**Status:** Draft
**Data:** 2026-02-XX
**Decide:** Política v1 de limitação de taxa e quotas por tenant
**Relacionados:** ADR 0004, ADR 0006, ADR 0007

---

## Contexto

Os ADRs 0004 e 0007 citam negação por política e exigem comportamento determinístico, auditável e tenant-aware.
Ainda não há contrato explícito para rate limiting/quotas, nem definição de onde essas políticas vivem e como são aplicadas de forma governada.

---

## Decisão a ser tomada

Definir um mecanismo v1 (policy-driven) para rate limiting e quotas por tenant, incluindo:
- local de definição da policy,
- comportamento de erro,
- sinais mínimos de auditoria/observabilidade.

---

## Fora de escopo

- billing e planos comerciais
- auto-scaling baseado em quotas

---

## Próximos passos

Definir e promover este ADR antes de materializar enforcement em Runtime/Control Plane.
