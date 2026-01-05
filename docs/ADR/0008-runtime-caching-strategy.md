# 📘 ADR 0008 — **Runtime Caching Strategy**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0008 — Runtime Caching Strategy**

## Context

O runtime do CONTRACTOR executa **compute-on-read** contra fontes externas. Sem cache, isso implica:

* latência elevada
* carga excessiva nos bancos dos clientes
* custo operacional alto
* risco de timeouts e experiências inconsistentes

Ao mesmo tempo, caching mal projetado em ambiente multi-tenant pode causar:

* vazamento cross-tenant
* respostas inconsistentes entre versões de bundle
* dados obsoletos ou semanticamente incorretos

## Decision

Adotar uma **estratégia de cache runtime-aware, tenant-scoped e bundle-scoped**, com invalidação determinística baseada em versão de artefatos.

### Princípios

1. **Cache is an optimization, never a source of truth**
2. **No cache without explicit scope**
3. **Cache correctness > cache hit ratio**

## Model

### Cache Scope (obrigatório)

Toda chave de cache **deve** incluir:

* `tenant_id`
* `bundle_id`
* `entity_id` ou `intent_id`
* hash dos parâmetros inferidos (ex.: janela temporal, filtros)

Exemplo lógico:

```
cache_key = hash(
  tenant_id,
  bundle_id,
  entity_id,
  inferred_params_fingerprint
)
```

### Cache Layers

* **L1 (in-process, opcional)**

  * curta duração
  * apenas para deduplicação de requests simultâneos
* **L2 (Redis / distributed cache)**

  * cache principal
  * segregado por tenant (prefix ou DB lógico)

Persistência em disco **não é permitida**.

### TTL Strategy

* TTL **policy-driven**, definida no bundle:

  * por entidade
  * por tipo de dado (snapshot vs historical)
* Default conservador (ex.: segundos/minutos), nunca infinito.
* Proibido TTL “hardcoded” em código.

### Cache Invalidation

* **Invalidação automática por bundle_id**

  * qualquer promoção (novo `current`) invalida cache anterior
* Invalidação manual:

  * via Control Plane (tenant_admin)
* Não existe “cache warming” automático no MVP.

## Alternatives Considered

### 1) No caching

**Cons:** inviável em produção; custo e latência altos.

### 2) Cache global sem bundle awareness

**Cons:** respostas semanticamente erradas após promoção; risco grave.

### 3) **Tenant + Bundle scoped cache (chosen)**

**Pros:** correção semântica, rollback seguro, isolamento forte.

## Implications

* Implementar `rt_cache` como serviço explícito no runtime
* Todas as chamadas ao executor passam por camada de cache
* Métricas obrigatórias:

  * cache_hit
  * cache_miss
  * cache_bypass
* Policies de cache são parte do bundle e versionadas

## Consequences

O cache deixa de ser “mágica invisível” e passa a ser **componente governado**, previsível e auditável — essencial para confiabilidade multi-tenant.

---
