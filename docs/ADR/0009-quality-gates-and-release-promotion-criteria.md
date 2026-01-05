# 📘 ADR 0009 — **Quality Gates and Release Promotion Criteria**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0009 — Quality Gates and Release Promotion Criteria**

## Context

CONTRACTOR permite que tenants editem contratos que afetam diretamente:

* roteamento semântico
* SQL executado
* respostas finais

Sem critérios formais de qualidade, uma promoção pode:

* quebrar produção
* gerar respostas incorretas
* introduzir riscos de segurança
* degradar confiança no produto

É necessário um **mecanismo objetivo e automatizável** para decidir se um bundle pode virar `current`.

## Decision

Adotar **Quality Gates obrigatórios** para promoção de bundles, com critérios mínimos e extensíveis por policy.

Promoção segue o fluxo:

```
draft → (validate + test) → candidate → (approve) → current
```

Nenhum bundle pode ser promovido sem **relatório de qualidade associado**.

## Quality Gates (v0)

### 1) Static Validation (blocking)

* YAML parse válido
* Schemas compatíveis
* Ontologia ↔ entidades ↔ templates consistentes
* Policies referenciadas existem
* Proibição de constructs inseguros (templates, SQL)

### 2) Routing Quality (blocking)

Executado via suites de roteamento:

* `routed_rate ≥ 0.98`
* `top1_accuracy ≥ 0.93` (MVP)
* `top2_gap_p50 ≥ 0.0` (ou policy-driven)

### 3) Entity Execution (blocking)

* Pelo menos 1 suite SQL-only por entidade crítica
* Execução real (LIMITed) sem erro
* Tipos e campos retornados compatíveis com contratos

### 4) Security Checks (blocking)

* Nenhuma entidade privada loga dados brutos
* Templates passam sandbox validation
* SQL sempre parametrizado
* Policies de redaction presentes

### 5) Non-blocking Checks (informational)

* Latência média
* Cache hit ratio estimado
* Custo relativo (heurístico, não impeditivo no MVP)

## Promotion Rules

* Falha em qualquer gate **bloqueia** promoção para `candidate`.
* `candidate` só pode virar `current` com:

  * aprovação explícita (manual ou policy)
  * registro em audit log
* Rollback é permitido a qualquer momento, sem revalidação.

## Alternatives Considered

### 1) Promoção manual sem gates

**Cons:** alto risco operacional; dependência humana.

### 2) Gates apenas em produção

**Cons:** impacto direto no usuário final.

### 3) **Gates formais antes da promoção (chosen)**

**Pros:** previsibilidade, confiança e automação.

## Implications

* Control Plane precisa de:

  * `QualityRunner`
  * `QualityReport` versionado por bundle
* UI deve mostrar:

  * status por gate (pass/fail)
  * métricas objetivas
* Policies podem ajustar thresholds por tenant/plano.

## Consequences

A qualidade deixa de ser subjetiva e passa a ser **contratual**.
Isso reduz incidentes, facilita rollback e sustenta crescimento enterprise.

---
