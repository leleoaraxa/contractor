# 📘 ADR 0023 — **Enterprise SLA Model**

**Status:** Draft
**Date:** 2026-01-13
**Stage:** 3 — Enterprise Ready
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0022 — Dedicated Runtime & Isolation Model
* STAGE_3_ENTERPRISE_READY.md

---

## Context

Com a introdução do **Dedicated Runtime por tenant** (ADR 0022), o CONTRACTOR passa a ter as **condições técnicas mínimas** para oferecer **compromissos contratuais formais** a clientes enterprise.

No Stage 2, a plataforma opera com **SLOs internos**, adequados para confiabilidade operacional, porém:

* não são contratuais
* não possuem penalidades
* não garantem exclusividade por tenant

Para clientes enterprise, é necessário definir um **modelo explícito de SLA (Service Level Agreement)** que seja:

* tecnicamente defensável
* operacionalmente mensurável
* juridicamente claro
* limitado em escopo (sem promessas irreais)

---

## Decision

Adotar um **Enterprise SLA Model** baseado em:

* **SLOs mensuráveis**
* **runtime dedicado por tenant**
* **escopo restrito a capacidades Stage 3**
* **penalidades contratuais proporcionais e limitadas**

O SLA será **opt-in**, disponível **exclusivamente para tenants Stage 3**.

---

## SLA Principles

1. **SLA is a contract, not a feature**
2. **No SLA without isolation**
3. **Measurable or it does not exist**
4. **Penalties are bounded**
5. **No SLA for experimental features**

---

## Scope of the SLA

### 1. Covered Services

O SLA cobre exclusivamente:

* **Runtime dedicado**

  * Endpoint: `/api/v1/runtime/ask`
* **Disponibilidade do runtime**
* **Latência agregada do runtime**

O Control Plane **não** está coberto por SLA no Stage 3.

---

### 2. Explicit Exclusions

O SLA **não cobre**:

* qualidade semântica das respostas
* precisão de dados de domínio
* falhas em integrações externas do tenant
* indisponibilidade causada por uso indevido do SDK/API
* períodos de manutenção previamente comunicados

---

## SLA Metrics

### 3. Availability

* Métrica: disponibilidade mensal do runtime dedicado
* Cálculo:

  ```
  availability = successful_requests / total_requests
  ```
* Status codes considerados indisponibilidade: `5xx`

---

### 4. Latency (Aggregate)

* Métrica: p95 de latência mensal
* Medida no runtime dedicado
* Janela: mensal (rolling window)

---

## SLA Targets (Stage 3 Defaults)

| Métrica                | Target |
| ---------------------- | ------ |
| Disponibilidade mensal | 99.9%  |
| Latência p95           | ≤ 2s   |

> Targets podem variar por contrato, **nunca acima do que a plataforma consegue medir**.

---

## Measurement & Evidence

* Métricas coletadas por:

  * Prometheus (runtime dedicado)
  * logs estruturados
* Relatórios mensais por tenant
* Dados de SLA são:

  * imutáveis após fechamento do período
  * auditáveis

O Control Plane é a **fonte oficial de relatórios de SLA**.

---

## Violation & Penalties

### 5. SLA Breach

Um breach ocorre quando:

* o target mensal não é atingido
* excluídas as janelas de manutenção acordadas

---

### 6. Penalty Model (Bounded)

Penalidades são:

* **financeiras**
* **limitadas**
* **não cumulativas**

Exemplo de modelo (referencial):

| Disponibilidade mensal | Crédito |
| ---------------------- | ------- |
| ≥ 99.9%                | 0%      |
| 99.5% – 99.89%         | 5%      |
| 99.0% – 99.49%         | 10%     |
| < 99.0%                | 20%     |

> Créditos nunca excedem o valor mensal do runtime dedicado.

---

## Incident & SLA Interaction

* Incidentes SEV-1 (ADR Incident Management):

  * impactam diretamente SLA
* Postmortems:

  * obrigatórios em breach
  * compartilháveis com o cliente (versão sanitizada)

---

## Tenant Responsibilities

Para validade do SLA, o tenant deve:

* utilizar exclusivamente o runtime dedicado
* respeitar limites contratuais de uso
* manter integrações externas saudáveis
* não subverter mecanismos de rate limit ou segurança

---

## Legal & Compliance Notes

* O SLA **não substitui**:

  * DPA
  * termos de privacidade (ADR 0018)
* CONTRACTOR permanece como **Data Processor**
* O tenant permanece como **Data Controller**

---

## Alternatives Considered

### 1) SLA global no runtime compartilhado

**Cons:** tecnicamente indefensável.

---

### 2) SLAs por feature

**Cons:** impossível medir de forma objetiva.

---

### 3) **SLA por runtime dedicado (chosen)**

**Pros:**

* mensurável
* auditável
* comercialmente claro
* alinhado ao Stage 3

---

## Consequences

* O produto passa a:

  * vender confiabilidade, não promessa
  * precificar isolamento e previsibilidade
* A engenharia ganha:

  * limites claros
  * menos exceções
* O comercial ganha:

  * contrato defensável
  * narrativa enterprise sólida

---

## Explicit Non-Goals

Este ADR **não define**:

* billing detalhado
* compensações legais específicas
* multi-região ativa-ativa
* disaster recovery (DR) formal

Esses temas exigem ADRs próprios.

---

## Final Notes

Sem este modelo, **Stage 3 não é comercialmente viável**.

Este ADR fecha o **tripé enterprise** do CONTRACTOR:

* isolamento (ADR 0022)
* SLA (ADR 0023)
* compliance (ADR 0018)

---
