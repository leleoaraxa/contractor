# 📘 ADR 0010 — **Planner and Ontology Resolution Strategy**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0010 — Planner and Ontology Resolution Strategy**

## Context

O CONTRACTOR deve interpretar linguagem natural e resolver **intent(s)** e **entity(ies)** de forma **determinística**, auditável e reproduzível. O Planner é o núcleo semântico do runtime; qualquer heurística oculta ou dependência de estado implícito compromete governança, qualidade e confiança.

## Decision

Adotar um **Planner ontology-driven**, com resolução baseada exclusivamente em **artefatos versionados** (ontologia, catálogo de entidades e policies), e **LLM como componente opcional e estritamente restrito**.

### Princípios

1. **Ontology is the contract**: toda resolução parte da ontologia do bundle.
2. **Determinism first**: mesma entrada + mesmo bundle ⇒ mesma decisão.
3. **LLM is assistive, never authoritative**: se usado, apenas para scoring auxiliar sob policy.

## Model

### Inputs do Planner

* `question`
* `tenant_id`
* `bundle_id`
* `policies.planner.*`
* contexto mínimo (ex.: idioma)

### Pipeline de Resolução

1. **Candidate Generation (deterministic)**

   * match por termos, sinônimos e regras declaradas na ontologia
   * expansão controlada por policy
2. **Scoring**

   * regras determinísticas (pesos declarados)
   * **opcional**: LLM scoring auxiliar (policy-driven, com fallback)
3. **Selection**

   * top-1/top-2 com cálculo de `gap`
   * aplicação de thresholds (quality gates)
4. **Routing Decision**

   * entity/intent selecionado
   * parâmetros inferidos (somente os permitidos por contrato)

### Proibições

* Heurísticas “temporárias” em código
* Ajustes por tenant fora de policy
* Dependência de estado histórico não versionado

## Alternatives Considered

1. Planner totalmente LLM-driven
2. Regras hardcoded por domínio
3. **Ontology-driven com LLM restrito (chosen)**

**Pros (chosen):**

* Reprodutibilidade
* Auditabilidade por bundle
* Controle fino por policy

**Cons:**

* Exige ontologia bem modelada
* Curva inicial maior

## Implications

* Ontologia deve declarar: intents, entities, termos, exclusões, pesos.
* Planner expõe **explain()** estruturado (inputs, scores, decisão).
* Métricas obrigatórias: `top1`, `top2_gap`, `routed_rate`.

## Consequences

O Planner torna-se um **componente contratual**. Melhorias semânticas ocorrem por artefatos, não por código.

---
