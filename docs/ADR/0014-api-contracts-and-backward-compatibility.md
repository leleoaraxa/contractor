# 📘 ADR 0014 — **API Contracts and Backward Compatibility**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0014 — API Contracts and Backward Compatibility**

## Context

CONTRACTOR expõe APIs críticas (Control Plane e Runtime) consumidas por:

* UIs
* automações de clientes
* integrações internas (quality runner, observability)
* possíveis SDKs futuros

Mudanças não controladas de API geram:

* quebra de clientes
* retrabalho operacional
* perda de confiança (especialmente enterprise)

É necessário definir **contratos explícitos**, regras de evolução e política clara de compatibilidade.

## Decision

Adotar **API contracts versioned-by-path**, com **compatibilidade retroativa garantida dentro da mesma versão major**, e mudanças breaking apenas via nova versão major.

### Princípios

1. **APIs are contracts, not implementation details**
2. **Backward compatibility is the default**
3. **Breaking changes require explicit versioning**

## Model

### Versioning Strategy

* Versionamento por path:

  ```
  /api/v1/control/...
  /api/v1/runtime/ask
  ```
* Incremento de versão **major** (`v1 → v2`) para breaking changes.
* Versões minor/patch não aparecem no path.

### Compatibility Rules (v1)

Mudanças **permitidas** (non-breaking):

* adicionar campos opcionais
* adicionar novos endpoints
* ampliar enums sem remover valores
* adicionar headers opcionais

Mudanças **proibidas** (breaking):

* remover campos
* alterar tipo/semântica de campos
* alterar comportamento padrão
* renomear endpoints
* alterar contratos de erro

### Deprecation Policy

* Endpoints/fields podem ser marcados como `deprecated`.
* Janela mínima de suporte:

  * definida por policy (ex.: 6–12 meses)
* Deprecação deve incluir:

  * alternativa clara
  * data-alvo de remoção
  * nota em changelog

### Schema Contracts

* OpenAPI é fonte de verdade para:

  * payloads
  * responses
  * erros
* Testes automatizados de contrato:

  * runtime vs OpenAPI
  * control plane vs OpenAPI

## Alternatives Considered

### 1) Sem versionamento explícito

**Cons:** quebra silenciosa, inviável para B2B.

### 2) Versionamento por header

**Cons:** debugging mais difícil; menos visível.

### 3) **Versioning by path (chosen)**

**Pros:** clareza, previsibilidade, padrão amplamente aceito.

## Implications

* Qualquer mudança potencialmente breaking exige:

  * novo ADR
  * nova versão major
  * plano de migração
* SDKs (se existirem) devem alinhar com major version.
* Quality suites devem validar contratos de API.

## Consequences

APIs do CONTRACTOR tornam-se **estáveis, confiáveis e previsíveis**, reduzindo churn técnico e facilitando adoção enterprise.

---
