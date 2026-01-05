# 📘 ADR 0011 — **Template Rendering and Output Safety Model**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0011 — Template Rendering and Output Safety Model**

## Context

Templates definem a apresentação final das respostas. Em ambiente multi-tenant, renderização insegura pode causar:

* execução arbitrária
* vazamento de dados
* inconsistência entre bundles
* dependência de código

## Decision

Adotar um **modelo de renderização sandboxed**, com **allowlist explícita** de recursos e **contratos de saída**.

### Princípios

1. **Templates are data, not code**
2. **Least privilege rendering**
3. **Output correctness over flexibility**

## Model

### Engine

* Jinja (ou equivalente) em **sandbox**
* Sem acesso a filesystem, rede, env ou builtins perigosos

### Allowlist

* Filtros explícitos (ex.: formatação, datas, currency)
* Funções utilitárias puras (sem I/O)
* Variáveis expostas: apenas `rows`, `meta`, `policies.output.*`

### Output Contract

* Templates devem produzir:

  * texto (Markdown/Plain) **ou**
  * estrutura declarada (ex.: JSON/Blocks), conforme policy
* Proibição de acessar campos não declarados no schema da entidade

### Validation

* Static:

  * parse do template
  * verificação de filtros/funções permitidas
* Dynamic:

  * render com payload mínimo (smoke test)

## Alternatives Considered

1. Templates livres (execução ampla)
2. Hardcode de outputs em código
3. **Sandbox + allowlist (chosen)**

**Pros (chosen):**

* Segurança
* Portabilidade entre tenants
* Evolução sem deploy

**Cons:**

* Menor flexibilidade criativa
* Exige catálogo de filtros bem mantido

## Implications

* Control Plane valida templates no upload.
* Runtime falha com erro claro se template violar sandbox.
* Catálogo de filtros é versionado e documentado.

## Consequences

A camada de apresentação passa a ser **segura, previsível e governada**, permitindo white label sem riscos.

---
