# 📘 ADR 0012 — **RAG Integration and Knowledge Boundaries**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0012 — RAG Integration and Knowledge Boundaries**

## Context

O CONTRACTOR pode integrar **Retrieval-Augmented Generation (RAG)** para enriquecer respostas com **conhecimento textual externo** (documentação, conceitos, explicações, contexto). Em plataformas analíticas multi-tenant, o uso irrestrito de RAG cria riscos claros:

* mistura de conhecimento factual com dados operacionais
* alucinação numérica
* vazamento de informações entre tenants
* quebra de determinismo

É necessário definir **fronteiras explícitas** entre:

* dados operacionais (SQL, métricas, resultados)
* conhecimento contextual (texto explicativo)

## Decision

Adotar um modelo de **RAG estritamente delimitado por policy**, onde:

* RAG **nunca** produz ou altera valores numéricos, métricas ou resultados
* RAG atua apenas como **camada explicativa ou contextual**
* o uso de RAG é **opt-in por bundle**

### Princípios

1. **Data first, knowledge second**
2. **No numeric authority outside SQL**
3. **RAG is additive, never corrective**

## Model

### Allowed RAG Domains

* conceitos
* definições
* explicações didáticas
* contexto regulatório ou histórico
* glossários
* notas interpretativas

### Forbidden RAG Domains

* cálculos
* métricas
* rankings
* valores monetários
* percentuais
* datas específicas oriundas de dados operacionais

### Integration Points

* RAG só pode ser invocado:

  * após execução SQL
  * após decisão do Planner
* RAG recebe apenas:

  * textos de contexto
  * nomes de entidades/intents
  * **nunca** recebe `rows` ou resultados numéricos

### Knowledge Isolation

* Índices RAG são:

  * segregados por tenant
  * versionados por bundle (ou alias controlado)
* Proibido acesso cruzado a índices de outros tenants.

## Alternatives Considered

### 1) RAG livre e global

**Cons:** alto risco de alucinação e vazamento.

### 2) RAG como substituto de SQL

**Cons:** quebra completa do modelo determinístico.

### 3) **RAG restrito por policy (chosen)**

**Pros:** previsibilidade, segurança, confiança.

## Implications

* Policies devem declarar:

  * `rag.enabled`
  * `rag.allowed_domains`
  * `rag.index_scope`
* Runtime valida que respostas numéricas vêm exclusivamente do executor SQL.
* Quality Gates devem incluir:

  * verificação de “numeric leakage” via RAG.

## Consequences

RAG torna-se um **componente auxiliar governado**, preservando determinismo e evitando alucinações — essencial para analytics B2B.

---
