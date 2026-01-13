# 📘 ADR 0036 — **Marketplace Trust, Reputation & Rating System**

**Status:** Draft
**Date:** 2026-01-13
**Stage:** 4 — Platform Ecosystem
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0029 — Stage 4 Platform Ecosystem Vision
* ADR 0030 — Bundle Marketplace Governance Model
* ADR 0035 — Marketplace Dispute Resolution & Legal Escalation Model

---

## Context

Em um marketplace com múltiplos **tenants**, **partners** e **bundles**, confiança não pode ser implícita.

Sem um sistema explícito de confiança e reputação, o ecossistema sofre de:

* assimetria de informação
* risco percebido elevado
* dependência excessiva de curadoria manual
* dificuldade de escalar o marketplace

É necessário um **modelo objetivo, gradual e auditável** para expressar confiança, sem criar obrigações legais implícitas.

---

## Decision

Adotar um **Trust, Reputation & Rating System**, onde:

* confiança é **derivada de sinais objetivos**
* reputação é **acumulativa e histórica**
* ratings são **informativos, não garantias**
* a plataforma **expõe sinais**, mas não certifica qualidade absoluta

---

## Princípios

1. **Trust is earned, not granted**
2. **Signals over opinions**
3. **No trust without history**
4. **Transparency without liability**
5. **Trust influences discovery, not execution**

---

## Entidades Avaliadas

O sistema se aplica a:

### 1) Partners

* desenvolvedores de bundles
* integradores certificados

### 2) Bundles

* artefatos distribuídos no marketplace

> Tenants **não são ranqueados** (evita efeitos adversos e conflitos).

---

## Fontes de Sinal (Inputs de Confiança)

### Sinais Técnicos (objetivos)

* taxa de falha
* incidentes associados
* compatibilidade com versões
* tempo médio de resolução
* histórico de rollback

### Sinais Operacionais

* cumprimento de SLAs (quando aplicável)
* resposta a incidentes
* reincidência de problemas

### Sinais de Governança

* violações de policy
* disputas recorrentes
* ações corretivas exigidas

### Sinais de Uso

* adoção ativa
* retenção
* desinstalações/reversões frequentes

---

## Sistema de Rating

### Natureza

* **Score agregado** (ex.: 0–100 ou níveis A/B/C)
* **Tendência** (subindo / estável / caindo)
* **Histórico visível** (não apenas o valor atual)

### Importante

* Ratings **não são avaliações subjetivas**
* Não há “reviews livres” no Stage 4 inicial
* Não há comentários públicos arbitrários

---

## Uso do Trust System

O trust score influencia:

* ordenação no marketplace
* destaque/recomendação
* elegibilidade para programas avançados
* visibilidade comercial

O trust score **não**:

* bloqueia execução técnica diretamente
* substitui quality gates
* altera contratos automaticamente

---

## Integração com Outros Sistemas

Este modelo se integra com:

* Incident Management
* Dispute Resolution
* Billing & Revenue
* Bundle Governance
* Audit Logs

Nenhum score é calculado sem **evidência rastreável**.

---

## Proteções contra Abuso

* scores não podem ser manipulados manualmente
* mudanças significativas exigem múltiplos sinais
* eventos extremos são ponderados no tempo
* disputas podem congelar ou ajustar temporariamente scores

---

## Entry Criteria

Este ADR se aplica quando:

* marketplace está ativo
* múltiplos partners coexistem
* bundles competem por adoção
* há histórico operacional suficiente

---

## Consequences

* Maior confiança no ecossistema
* Menor fricção de adoção
* Incentivos corretos para qualidade
* Redução de curadoria manual

---

## Explicit Non-Goals

Este ADR **não define**:

* certificações formais
* garantias de resultado
* responsabilidade legal por ratings
* mecanismos de review social aberto

---

## Final Statement

> **Trust scales ecosystems faster than control — when built on evidence.**

Este ADR estabelece uma base objetiva e defensável para confiança no marketplace, sem criar passivos legais ou dependência subjetiva.

---
