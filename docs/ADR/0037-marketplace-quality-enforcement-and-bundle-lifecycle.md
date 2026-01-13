# 📘 ADR 0037 — **Marketplace Quality Enforcement & Bundle Lifecycle**

**Status:** Draft
**Date:** 2026-01-13
**Stage:** 4 — Platform Ecosystem

**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0029 — Stage 4 Platform Ecosystem Vision
* ADR 0030 — Bundle Marketplace Governance Model
* ADR 0036 — Marketplace Trust, Reputation & Rating System

---

## Context

Com a introdução de um marketplace aberto, bundles deixam de ser apenas artefatos técnicos e passam a ter **impacto sistêmico** no ecossistema.

Sem um modelo explícito de **ciclo de vida e enforcement de qualidade**, o marketplace corre risco de:

* degradação progressiva da qualidade média
* acúmulo de bundles obsoletos ou inseguros
* incentivos desalinhados para manutenção
* sobrecarga de curadoria manual

É necessário um **modelo formal, previsível e auditável** de lifecycle e enforcement.

---

## Decision

Adotar um **Bundle Lifecycle Model**, com estágios explícitos, regras de transição claras e enforcement automático baseado em evidências operacionais.

O sistema:

* define estados canônicos de bundles
* conecta qualidade operacional ao lifecycle
* integra trust/reputation como sinal, não como decisão única
* preserva previsibilidade para parceiros e tenants

---

## Princípios

1. **Quality is enforced, not assumed**
2. **Lifecycle is explicit**
3. **Signals drive transitions**
4. **No silent failures**
5. **Enforcement before removal**

---

## Estados do Lifecycle do Bundle

### 1) Draft

* Bundle em desenvolvimento
* Não listado publicamente
* Uso restrito a testes internos ou tenants autorizados

---

### 2) Published

* Bundle disponível no marketplace
* Elegível para adoção
* Sujeito a monitoramento contínuo

---

### 3) Active

* Bundle com uso real em produção
* Métricas operacionais válidas
* Participa do sistema de trust/reputation

---

### 4) Degraded

* Bundle com sinais negativos recorrentes
* Pode incluir:

  * incidentes frequentes
  * violações de policy
  * queda acentuada de trust score
* Visibilidade reduzida no marketplace

---

### 5) Deprecated

* Bundle funcional, porém:

  * tecnicamente obsoleto
  * incompatível com versões recentes
  * substituído por alternativa superior
* Novas adoções desincentivadas

---

### 6) Suspended

* Bundle temporariamente indisponível
* Causas típicas:

  * incidentes críticos
  * violações graves
  * disputas abertas
* Execuções existentes podem continuar conforme policy

---

### 7) Retired

* Bundle removido do marketplace
* Não disponível para novas execuções
* Mantido apenas para histórico/auditoria

---

## Regras de Transição

Transições são acionadas por:

* métricas operacionais
* eventos de incident management
* decisões de governança
* solicitações do partner (quando permitido)

> Nenhuma transição ocorre sem **registro em audit log**.

---

## Quality Enforcement Mechanisms

### Sinais utilizados

* incidentes (SEV-1 / SEV-2)
* violações de SLO
* falhas recorrentes
* incompatibilidade técnica
* disputas confirmadas

### Ações de enforcement

* redução de visibilidade
* alertas ao partner
* congelamento de novas adoções
* suspensão temporária
* retirada definitiva

---

## Integração com Trust System

* Trust score **não decide sozinho**
* Trust score **amplifica sinais**
* Lifecycle changes impactam trust score
* Histórico é preservado mesmo após retirada

---

## Proteções para Tenants

* Bundles degradados ou suspensos **não são removidos silenciosamente**
* Tenants recebem:

  * avisos prévios
  * janelas de migração
  * recomendações alternativas (quando existirem)

---

## Entry Criteria

Este ADR entra em vigor quando:

* marketplace ativo
* múltiplos bundles concorrentes
* sinais operacionais confiáveis
* trust system operacional (ADR 0036)

---

## Explicit Non-Goals

Este ADR **não define**:

* regras comerciais
* precificação ou revenue split
* certificações formais
* SLA específico por bundle

---

## Consequences

* Qualidade média do marketplace cresce com o tempo
* Incentivos corretos para manutenção
* Menor dependência de curadoria manual
* Redução de risco sistêmico

---

## Final Statement

> **An ecosystem without lifecycle discipline eventually collapses under its own entropy.**

Este ADR garante que o marketplace evolua de forma sustentável, previsível e defensável.

---
