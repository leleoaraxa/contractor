# 📘 ADR 0033 — **Marketplace Billing, Invoicing & Financial Reconciliation**

**Status:** Draft
**Date:** 2026-01-13
**Stage:** 4 — Platform Ecosystem
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0029 — Stage 4 Platform Ecosystem Vision
* ADR 0030 — Bundle Marketplace Governance Model
* ADR 0031 — Partner & Integrator Lifecycle Model
* ADR 0032 — Marketplace Commercial & Revenue Model

---

## Context

Após definir:

* **governança do marketplace** (ADR 0030)
* **ciclo de vida de parceiros** (ADR 0031)
* **modelo comercial e revenue share** (ADR 0032)

o CONTRACTOR precisa operacionalizar **como o dinheiro é medido, cobrado, distribuído e reconciliado**.

Sem um modelo explícito de **billing e reconciliação**, surgem riscos graves:

* divergência entre uso real e cobrança
* disputas financeiras com parceiros
* impossibilidade de auditoria
* fragilidade legal e operacional

O Stage 4 exige um **sistema financeiro técnico, auditável e previsível**.

---

## Decision

Adotar um **Marketplace Billing & Financial Reconciliation Model** baseado em:

* **metering técnico como fonte de verdade**
* **billing determinístico e reproduzível**
* **reconciliação explícita entre platform ↔ partner**
* **separação clara entre cálculo, faturamento e pagamento**

Este ADR define o **modelo técnico-operacional**, não sistemas financeiros externos específicos.

---

## Princípios

1. **Metering is law**
2. **Billing must be replayable**
3. **No hidden adjustments**
4. **Disputes resolved by data, not opinion**
5. **Finance follows platform reality**

---

## Componentes do Modelo

### 1. Metering (Fonte de Verdade)

O metering é derivado exclusivamente de:

* execuções reais do runtime
* resolução efetiva de `bundle_id` / `version`
* consumo de recursos associado à execução

Características:

* imutável após registro
* versionado
* atribuível a tenant, bundle e partner

---

### 2. Usage Ledger (Ledger de Uso)

A plataforma mantém um **ledger técnico**, contendo:

* tenant_id
* bundle_id / version
* partner_id (quando aplicável)
* tipo de uso (request, compute, feature)
* quantidade
* timestamp

Este ledger **não é financeiro**, mas **é a base de toda cobrança**.

---

### 3. Billing Engine

O Billing Engine:

* aplica regras do ADR 0032
* converte uso → valores monetários
* gera faturas técnicas (billing statements)

Características:

* determinístico
* versionado por policy
* replayável a partir do ledger

---

### 4. Invoicing

O sistema gera:

* **Invoice para Tenant** (cobrança total)
* **Statement para Partner** (direito a receber)

Notas importantes:

* invoices são **derivadas**, nunca manuais
* alterações exigem novo ciclo documentado
* histórico é imutável

---

### 5. Revenue Split & Settlement

Com base nos invoices:

* calcula-se o revenue share
* gera-se o **partner settlement**
* a plataforma retém sua parte

O pagamento efetivo pode ocorrer:

* fora da plataforma
* via sistemas financeiros externos

---

## Reconciliação Financeira

### Objetivo

Garantir que:

> **Uso real = cobrança = distribuição**

### Processo

1. Ledger técnico é congelado para o período
2. Billing engine calcula valores
3. Invoices e statements são emitidos
4. Partner pode auditar os dados
5. Divergências são tratadas por replay técnico

---

## Auditoria e Disputas

* Toda cobrança deve ser **explicável por dados**
* Partners têm acesso ao ledger referente aos seus bundles
* Não existem “ajustes manuais silenciosos”

Disputas seguem este fluxo:

1. Contestação baseada em dados
2. Replay do billing
3. Correção documentada (se aplicável)

---

## Enforcement Técnico

* Bundles sem licença válida **não executam**
* Uso fora de contrato **não é faturado**
* Billing rules são aplicadas automaticamente

Não há cobrança baseada apenas em intenção ou contrato verbal.

---

## Explicit Non-Goals

Este ADR **não define**:

* gateways de pagamento
* impostos e tributos
* câmbio internacional
* contabilidade legal
* repasses bancários

Esses temas exigem ADRs financeiros e legais específicos.

---

## Entry Criteria

Este modelo entra em vigor quando:

* metering confiável estiver ativo
* marketplace estiver operacional
* revenue share definido (ADR 0032)
* mecanismos de auditoria disponíveis

---

## Consequences

* Cobrança transparente e defensável
* Redução de disputas financeiras
* Confiança entre platform e parceiros
* Base sólida para escala global

---

## Final Statement

> **Billing não é financeiro. Billing é engenharia.**

Este ADR transforma execução técnica em **realidade econômica verificável**, sustentando o ecossistema do CONTRACTOR em escala.

---
