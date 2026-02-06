# ADR 0019 — Promoção e rollback v1 (workflow de aliases e invariantes)

**Status:** Draft  
**Data:** 2026-02-06  
**Decide:** Contrato mínimo de promoção e rollback no Control Plane  
**Relacionados:** ADR 0003, ADR 0006, ADR 0011, ADR 0014, ADR 0016

---

## Contexto

ADR 0003 define aliases por tenant (`draft/candidate/current`), porém não formalizava o workflow governado
para alterar `current` com vínculo obrigatório a quality gate.

Este ADR define o contrato mínimo e determinístico v1 para:

- set de `candidate`;
- promoção (`candidate -> current`);
- rollback explícito (`current -> bundle_id` alvo);
- invariantes tenant-aware e fail-closed;
- auditoria obrigatória por operação.

---

## Decisão

### 1) Endpoints v1

- `POST /tenants/{tenant_id}/aliases/candidate`
  - body: `{ "bundle_id": "..." }`
  - efeito: define `candidate` (idempotente)
- `POST /tenants/{tenant_id}/aliases/promote`
  - body vazio
  - efeito: `current <- candidate`
- `POST /tenants/{tenant_id}/aliases/rollback`
  - body: `{ "bundle_id": "..." }`
  - efeito: `current <- bundle_id` alvo

### 2) Invariantes obrigatórias

- todas as operações são tenant-aware com auth do ADR 0011;
- `current` só muda via `promote` ou `rollback`;
- `promote` exige `candidate` definido;
- `promote` e `rollback` exigem gate aprovado (`outcome=pass`) para o mesmo
  `tenant_id` e o mesmo `bundle_id` alvo;
- operações são idempotentes quando `from == to`.

### 3) Persistência local v1

- armazenamento local por tenant:
  `data/control_plane/alias_state/{tenant_id}.json`;
- escrita atômica (`.tmp` + `replace`);
- schema v1:

```json
{
  "tenant_id": "tenant_a",
  "aliases": {
    "candidate": { "bundle_id": "demo-faq-0001" },
    "current": { "bundle_id": "demo-faq-0001" }
  }
}
```

`candidate` e `current` podem ser `null`.

### 4) Requisito de gate aprovado (consumo de ADR 0016)

Lookup local em:

`data/control_plane/gates/{tenant_id}/{bundle_id}/*.json`

A transição só é permitida quando existir ao menos um resultado persistido com:

- `tenant_id` igual ao tenant da rota;
- `bundle_id` igual ao bundle alvo;
- `outcome == "pass"`.

Não há mudança no contrato de gates; apenas consumo de resultado persistido.

### 5) Auditoria

Cada operação emite **1 evento** no padrão ADR 0014:

- `event in {"alias_candidate_set", "alias_promote", "alias_rollback"}`
- `ts_utc`, `service=control_plane`, `tenant_id`, `request_id`, `actor=control_plane_api`
- `outcome`, `http_status`, `latency_ms`
- `from_bundle_id` e `to_bundle_id` quando aplicável

Fail-closed: erro de auditoria retorna `500`.

---

## Contratos de erro v1

- `401` credenciais ausentes/inválidas
- `403` mismatch de tenant no token/header/path
- `404` bundle inexistente (set de candidate)
- `409` invariantes não satisfeitas (candidate ausente, gate não aprovado)
- `422` body inválido
- `500` configuração ausente/inválida ou storage inválido (fail-closed)

---

## Fora de escopo

- auto-rollback
- chamada Runtime durante promote/rollback
- persistência em banco/redis
- alteração do contrato de gates (ADR 0016)

---

## Consequências

### Positivas

- workflow mínimo governado para alterar alias `current`;
- vínculo explícito entre gate aprovado e transição de alias;
- trilha de auditoria por operação.

### Trade-offs

- estado local por arquivo é suficiente para v1, mas limitado para multi-instância;
- `resolve_current` legado não é alterado neste ADR (convivência temporária de stores).
