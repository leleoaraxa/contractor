# 📘 ADR 0032 — **Marketplace Commercial & Revenue Model**

**Status:** Draft
**Date:** 2026-01-13
**Stage:** 4 — Platform Ecosystem
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0029 — Stage 4 Platform Ecosystem Vision
* ADR 0030 — Bundle Marketplace Governance Model
* ADR 0031 — Partner & Integrator Lifecycle Model

---

## Context

Com o **Marketplace ativo** (ADR 0030) e o **ciclo de vida de parceiros definido** (ADR 0031), o CONTRACTOR entra na fase em que:

* bundles passam a ter **valor econômico**
* parceiros investem tempo e capital
* tenants esperam previsibilidade comercial
* a plataforma precisa sustentar sua operação

Sem um **modelo comercial explícito**, surgem riscos críticos:

* incentivos desalinhados
* conflitos entre parceiros e plataforma
* monetização improvisada
* perda de confiança no ecossistema

É necessário definir **como o dinheiro circula**, **quem paga**, **quem recebe** e **o que é permitido** no Stage 4.

---

## Decision

Adotar um **Marketplace Commercial & Revenue Model** explícito, baseado em:

* separação clara entre **capacidade técnica** e **modelo comercial**
* múltiplos tipos de monetização
* transparência de revenue share
* enforcement técnico via platform rules (não contratos implícitos)

Este ADR define o **modelo econômico de referência**, não contratos jurídicos finais.

---

## Princípios

1. **Revenue follows value**
2. **No hidden monetization**
3. **Technical enforcement over trust**
4. **Stage-aware commercialization**

---

## Atores Econômicos

### Platform (CONTRACTOR)

* Opera o marketplace
* Fornece runtime, control plane e isolamento
* Aplica regras de governança e billing

---

### Partner / Integrator

* Cria bundles, soluções ou serviços
* Pode monetizar diretamente ou via marketplace
* Assume responsabilidades definidas no ADR 0031

---

### Tenant (Cliente Final)

* Consome bundles e soluções
* Paga pela execução, capacidade e/ou licenças
* Não negocia diretamente regras internas do marketplace

---

## Tipos de Monetização

### 1. Platform Usage Fees

Cobrança pelo uso da plataforma:

* requests ao runtime
* consumo de recursos
* ambientes dedicados
* features enterprise

**Sempre cobrados pelo CONTRACTOR**, independentemente de bundles.

---

### 2. Bundle Licensing

Bundles podem ser:

* gratuitos
* pagos (licença fixa)
* pagos por uso (usage-based)

Licenças são **associadas ao bundle_id/version**, não ao código-fonte.

---

### 3. Revenue Share

Quando um bundle pago é consumido:

* uma parte vai para o Partner
* uma parte fica com a Platform

O split é **explícito, versionado e auditável**.

---

### 4. Professional Services (Out of Scope)

* Implementação
* Customização
* Operação

Não são cobrados via marketplace técnico neste estágio.

---

## Modelo de Revenue Share (Base)

Modelo de referência (ajustável futuramente):

| Item     | Percentual |
| -------- | ---------- |
| Partner  | 70%        |
| Platform | 30%        |

Notas:

* Pode variar por nível de certificação
* Pode variar por tipo de bundle
* Mudanças exigem versionamento e aviso prévio

---

## Billing & Metering

### Fonte de Verdade

* Execução real no runtime
* Resolução de bundle via control plane
* Métricas de uso auditáveis

### Princípios

* **Compute-based billing**
* **No black boxes**
* **Replayable calculations**

---

## Enforcement Técnico

O modelo comercial é aplicado por:

* policies de billing
* validação de bundles
* controle de execução no runtime
* bloqueio de bundles não licenciados

Não depende apenas de contratos.

---

## Governança Comercial

* Cada bundle declara seu modelo de monetização
* Alterações exigem nova versão
* Tenants aceitam termos no momento da ativação
* Histórico comercial é imutável

---

## Explicit Non-Goals

Este ADR **não define**:

* impostos
* faturamento internacional
* contratos jurídicos
* cobrança direta entre parceiros e clientes
* pagamentos off-platform

Esses temas exigem ADRs legais/financeiros específicos.

---

## Entry Criteria

Este ADR só entra em vigor quando:

* ADRs 0030 e 0031 estiverem **Accepted**
* Marketplace funcional
* Billing técnico confiável
* Mecanismos de auditoria ativos

---

## Consequences

* Monetização previsível e defensável
* Incentivos alinhados entre plataforma e parceiros
* Base sólida para crescimento sustentável
* Preparação para expansão enterprise e global

---

## Final Statement

> **Sem um modelo comercial explícito, marketplaces se tornam disputas políticas.**

Este ADR estabelece o **contrato econômico do ecossistema CONTRACTOR**.
Qualquer evolução (pricing avançado, descontos, planos complexos) exigirá novos ADRs.

---
