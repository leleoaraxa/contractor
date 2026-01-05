# 📘 ADR 0017 — **Billing, Metering and Commercial Plans**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0017 — Billing, Metering and Commercial Plans**

## Context

CONTRACTOR consome recursos variáveis:

* execução SQL (tempo e volume)
* cache e storage
* chamadas a LLM/RAG
* processamento e observabilidade

Para viabilidade comercial e escala sustentável, é necessário:

* medir uso real
* associar custo a tenant
* oferecer planos claros
* evitar custos imprevisíveis

## Decision

Adotar um modelo **metering-first**, onde **billing é derivado de métricas confiáveis**, com planos comerciais baseados em **quotas e limites contratuais**.

### Princípios

1. **Measure before charging**
2. **Usage-based transparency**
3. **Plans are contracts, not suggestions**

## Metering Model

### Metered Dimensions (v0)

Por tenant, medir:

* número de requests (/ask)
* tempo total de execução SQL
* volume estimado de dados processados
* tokens LLM (input/output)
* execuções de quality suites

Essas métricas são:

* agregadas por período (ex.: diário/mensal)
* imutáveis após fechamento do período
* auditáveis

### Cost Attribution

* Cada dimensão tem custo unitário configurável.
* Custo total do tenant é soma ponderada das dimensões.
* Cálculo é **determinístico e reprodutível**.

## Commercial Plans

### Plan Structure (exemplo)

* **Starter**

  * limites baixos
  * sem Agent
  * sem isolamento dedicado
* **Pro**

  * limites médios
  * RAG habilitado
  * suporte a Agent
* **Enterprise**

  * limites customizados
  * runtime dedicado
  * SLAs e compliance avançados

Planos definem:

* quotas
* rate limits
* features habilitadas
* políticas padrão

### Enforcement

* Quotas são hard limits no MVP.
* Ao atingir limite:

  * requests são bloqueadas
  * tenant recebe erro explícito
* Overages e cobrança excedente são opcionais (fase futura).

## Alternatives Considered

### 1) Billing fixo por tenant

**Cons:** injusto; não escala bem.

### 2) Billing baseado apenas em requests

**Cons:** ignora custo real (SQL, LLM).

### 3) **Metering multi-dimensional (chosen)**

**Pros:** justo, transparente, escalável.

## Implications

* Control Plane deve:

  * agregar métricas de uso
  * expor relatórios por tenant
  * integrar futuramente com sistema de billing externo
* Runtime deve:

  * registrar métricas de uso com precisão
  * garantir consistência mesmo sob falhas

## Consequences

Billing passa a ser **previsível, auditável e alinhado ao custo real**, viabilizando crescimento sustentável e ofertas enterprise.

---
