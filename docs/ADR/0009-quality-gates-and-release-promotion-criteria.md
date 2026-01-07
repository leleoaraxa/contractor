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

Adotar **Quality Gates obrigatórios** para promoção de bundles, com critérios mínimos e extensíveis por tenant.

Promoção segue o fluxo:

```
draft → (validate) → candidate → (validate + suites) → current
```

Nenhum bundle pode ser promovido para `candidate` ou `current` sem **relatório de qualidade associado**.

## Quality Gates (v0)

### 1) Static Validation (blocking)

* YAML parse válido
* Schemas compatíveis
* Ontologia ↔ entidades ↔ templates consistentes
* Policies referenciadas existem

### 2) Routing/Threshold Suites (blocking)

Executado via suites declaradas em `data/quality/suites/*.json`, por exemplo:

* `demo_routing_candidate_suite.json`
* `demo_thresholds_suite.json`
* `demo_routing_suite.json`
* `demo_pipeline_suite.json`

A lista de suites exigidas por tenant é definida em `registry/control_plane/promotion_sets/<tenant>.yaml`.

### 3) Execução SQL (blocking quando aplicável)

* Execução real (LIMITed) sem erro via `PostgresExecutor`.
* Erros de execução interrompem a promoção.

## Promotion Rules

* `draft` exige apenas validação.
* `candidate` e `current` exigem validação + suites obrigatórias.
* A promoção com gate é aplicada nos endpoints `/api/v1/control/tenants/{tenant_id}/aliases/*`.
* O mapeamento simples de aliases usado pelo runtime fica em `/api/v1/control/tenants/{tenant_id}/versions/*`.

## Operação e scripts

* `scripts/quality/run_routing_suite.py` executa suites isoladas contra o runtime.
* `scripts/quality/smoke_quality_gate.py` exercita o fluxo completo (healthz → qualidade → promotion gate).

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
  * `PromotionSetRepository` por tenant
* UI deve mostrar:

  * status por gate (pass/fail)
  * métricas objetivas
* Policies podem ajustar thresholds por tenant/plano.

## Consequences

A qualidade deixa de ser subjetiva e passa a ser **contratual**.
Isso reduz incidentes, facilita rollback e sustenta crescimento enterprise.

---
