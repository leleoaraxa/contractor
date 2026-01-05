# 📘 ADR 0021 — **Product Roadmap and Maturity Stages**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0021 — Product Roadmap and Maturity Stages**

## Context

CONTRACTOR é uma plataforma ambiciosa, com múltiplos eixos:

* técnica (runtime, control plane)
* operacional (SLOs, segurança)
* comercial (planos, billing)
* ecossistema (SDKs, parceiros)

Sem um **modelo explícito de maturidade**, há risco de:

* escopo inflado
* expectativas desalinhadas
* venda de features imaturas
* retrabalho por “atalhos” iniciais

É necessário definir **estágios claros de maturidade**, com critérios objetivos.

## Decision

Adotar um **modelo de Product Maturity Stages**, com roadmap orientado a **capacidades**, não a features isoladas.

### Princípios

1. **Capabilities before scale**
2. **Maturity is explicit**
3. **No enterprise promises without enterprise foundations**

## Maturity Stages

### Stage 0 — Foundation

**Objetivo:** viabilidade arquitetural

* runtime funcional
* control plane básico
* bundles e versionamento
* quality gates mínimos
* tenant Araquem como referência

❌ Não comercial

---

### Stage 1 — MVP (Early Adopters)

**Objetivo:** uso real controlado

* multi-tenant pool
* conexão direta a dados
* cache e rate limits
* observability básica
* billing interno (metering)

⚠️ Comercial limitado (design partners)

---

### Stage 2 — Production Ready

**Objetivo:** confiabilidade e governança

* SLOs ativos
* incident management
* rollback completo
* SDKs estáveis
* políticas de privacidade e retenção

✅ Comercial geral (SMB / Pro)

---

### Stage 3 — Enterprise Ready

**Objetivo:** escala e compliance

* runtime dedicado
* agent de dados
* isolamento avançado
* SLAs contratuais
* auditoria e compliance completos

✅ Enterprise

---

### Stage 4 — Platform Ecosystem

**Objetivo:** expansão e lock-in positivo

* marketplace de bundles
* parceiros e integradores
* automação avançada
* billing sofisticado

🚀 Escala e ecossistema

## Roadmap Governance

* Cada stage tem:

  * critérios de entrada
  * critérios de saída
* Feature não pode “pular” estágio.
* Marketing e vendas devem referenciar o estágio atual.

## Alternatives Considered

### 1) Roadmap baseado apenas em features

**Cons:** perda de coerência e qualidade.

### 2) Prometer enterprise cedo

**Cons:** dívida técnica e reputacional.

### 3) **Stage-based maturity model (chosen)**

**Pros:** alinhamento técnico, comercial e operacional.

## Implications

* Planejamento trimestral deve mapear features → stages.
* Documentação pública deve indicar estágio atual.
* Vendas só podem prometer capacidades do stage vigente.

## Consequences

O roadmap deixa de ser aspiracional e passa a ser **realista, defensável e sustentável**, alinhando engenharia, produto e negócio.

---
