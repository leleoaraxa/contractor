
# 📘 ADR 0015 — **Deployment Environments and Release Lifecycle**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0015 — Deployment Environments and Release Lifecycle**

## Context

CONTRACTOR possui múltiplos componentes (Control Plane, Runtime, Registry, Ops) e atende múltiplos tenants. Sem um ciclo de ambientes bem definido, surgem:

* promoções inseguras
* divergência entre ambientes
* testes incompletos
* incidentes em produção

É necessário padronizar **ambientes**, **promoções** e **rollback**.

## Decision

Adotar um **release lifecycle multi-environment**, com **promoção progressiva e gates obrigatórios**, alinhado ao modelo de bundles e quality gates.

### Princípios

1. **Same code, different config**
2. **Promote artifacts, not rebuild**
3. **Rollback is a first-class operation**

## Environments

### Defined Environments

* **local**

  * desenvolvimento
  * registry local
  * tenants de teste
* **dev**

  * integração contínua
  * testes automatizados
* **stage**

  * espelho de produção
  * testes de carga, segurança e regressão
* **prod**

  * ambiente de clientes
  * mudanças altamente controladas

Nenhum ambiente extra sem ADR.

## Release Units

### Code Release

* Control Plane
* Runtime
* Agents (quando existirem)

### Artifact Release

* Bundles por tenant
* Independentes do deploy de código

Code e artifacts **não** precisam ser promovidos juntos.

## Promotion Flow

### Code

```
local → dev → stage → prod
```

* Promoção exige:

  * testes unitários + integração
  * suites de regressão (tenant Araquem)
  * aprovação explícita para prod

### Artifacts (Bundles)

```
draft → candidate → current
```

* Promoção ocorre **dentro do mesmo ambiente**
* Bundles podem ser promovidos sem novo deploy

## Rollback Strategy

* **Code rollback**:

  * deploy da versão anterior
* **Artifact rollback**:

  * trocar alias `current` para bundle anterior
  * operação atômica e imediata

Rollback de artifacts **não exige** rollback de código.

## Alternatives Considered

### 1) Ambiente único

**Cons:** alto risco, sem isolamento.

### 2) CI/CD sem stage

**Cons:** testes incompletos.

### 3) **Multi-environment lifecycle (chosen)**

**Pros:** previsibilidade, segurança, maturidade operacional.

## Implications

* Infra deve suportar:

  * configs por ambiente
  * isolamento de secrets
* Dashboards e métricas devem ser environment-aware.
* Stage deve ter carga representativa (não “fake”).

## Consequences

O ciclo de release torna-se **seguro, auditável e repetível**, reduzindo incidentes e permitindo evolução contínua do CONTRACTOR.

---
