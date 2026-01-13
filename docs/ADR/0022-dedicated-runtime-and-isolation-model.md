Perfeito. Vou seguir **no caminho correto**, sem atalhos, e entregar **o ADR 0022 completo e canônico**, pronto para você criar o arquivo e commitar.

Abaixo está o conteúdo exato do:

---

# 📘 ADR 0022 — **Dedicated Runtime & Isolation Model**

**Status:** Draft
**Date:** 2026-01-13
**Stage:** 3 — Enterprise Ready
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* STAGE_3_ENTERPRISE_READY.md

---

## Context

No Stage 3 (Enterprise Ready), o CONTRACTOR passa a atender clientes com requisitos formais de:

* isolamento operacional
* previsibilidade de performance
* mitigação de risco entre tenants
* compromissos contratuais (SLAs)

O modelo atual (Stage 2) utiliza **runtime compartilhado**, adequado para SMB/Pro, porém **insuficiente** para requisitos enterprise, pois:

* falhas ou picos de carga de um tenant podem impactar outros
* não há garantias fortes de isolamento de recursos
* SLAs contratuais não são defensáveis sem isolamento explícito

É necessário definir **um modelo claro e explícito de isolamento de runtime**, sem introduzir complexidade desnecessária ou promessas prematuras.

---

## Decision

Adotar um **Dedicated Runtime Model** para tenants enterprise, baseado em **isolamento explícito por tenant**, mantendo os princípios centrais do CONTRACTOR:

* bundles imutáveis
* aliases (`draft / candidate / current`)
* determinismo operacional
* rollback como troca de alias

O modelo de isolamento será **opt-in e por tenant**, exclusivo do Stage 3.

---

## Isolation Model

### 1. Definition

Um **Dedicated Runtime** é uma instância de runtime que:

* executa requests de **um único tenant**
* resolve apenas bundles pertencentes a esse tenant
* possui isolamento operacional em relação a outros runtimes
* mantém o mesmo contrato de API do runtime compartilhado

Não há divergência de API entre runtime dedicado e compartilhado.

---

### 2. Scope of Isolation

O isolamento se aplica a:

* execução do `/api/v1/runtime/ask`
* cache runtime
* filas, workers e recursos de execução
* limites de rate e throughput

O isolamento **não** se aplica a:

* Control Plane (continua compartilhado)
* Registry de bundles (continua centralizado)
* Artefatos imutáveis (ontologia, policies, templates)

---

## Architectural Principles

### 3.1 Determinism First

* O runtime dedicado não altera:

  * formato de payload
  * lógica de planejamento
  * contratos de resposta
* Apenas o **ambiente de execução** muda.

---

### 3.2 No Hidden Multi-Tenancy

* Um runtime dedicado **nunca** atende múltiplos tenants.
* Não há “partições lógicas” ocultas.
* O isolamento é **explícito e auditável**.

---

### 3.3 Control Plane as Source of Truth

* O Control Plane:

  * provisiona runtimes dedicados
  * associa runtime ⇄ tenant
  * governa aliases e bundles
* O runtime é **stateless em relação à governança**.

---

## Operational Model

### 4. Provisioning

* Runtimes dedicados são:

  * criados sob demanda
  * associados explicitamente a um tenant
* O mecanismo exato de provisionamento (containers, VMs, etc.) **não é definido neste ADR**.

---

### 5. Routing

* Requests de um tenant enterprise:

  * são roteados exclusivamente para seu runtime dedicado
* Nenhum fallback automático para runtime compartilhado.

---

### 6. Failure Isolation

* Falhas em um runtime dedicado:

  * não afetam outros tenants
  * não afetam runtimes compartilhados
* Incidentes são **localizados por tenant**.

---

## SLOs and SLAs

* O runtime dedicado permite:

  * SLOs específicos por tenant
  * conversão de SLO → SLA contratual
* Métricas e alertas são segregados por tenant.

---

## Security & Compliance

* Runtime dedicado reforça:

  * isolamento de dados em memória
  * isolamento de cache
  * previsibilidade para auditorias
* O CONTRACTOR permanece como **Data Processor** (ADR 0018).

---

## Alternatives Considered

### 1) Runtime compartilhado com limites mais rígidos

**Cons:** isolamento fraco; SLAs indefensáveis.

---

### 2) Multi-tenant lógico no mesmo runtime

**Cons:** complexidade alta; difícil auditoria; risco residual.

---

### 3) **Dedicated Runtime por tenant (chosen)**

**Pros:**

* isolamento claro
* modelo simples de explicar
* base sólida para enterprise
* compatível com arquitetura existente

---

## Consequences

* Aumento de custo operacional por tenant enterprise
* Maior previsibilidade e defensabilidade comercial
* Base técnica sólida para:

  * SLAs
  * compliance
  * expansão futura (Stage 4)

Este custo é **intencional e alinhado ao posicionamento enterprise**.

---

## Explicit Non-Goals

Este ADR **não define**:

* tecnologia de orquestração
* modelo de billing
* estratégia de multi-região
* automação de canary ou rollout avançado

Esses temas exigem ADRs próprios.

---

## Follow-ups (Future ADRs)

* ADR 0023 — Enterprise SLA Model
* ADR 0024 — Tenant-Level Observability
* ADR 0025 — Secure Runtime Provisioning

---

## Final Notes

Este ADR estabelece **o pilar técnico central do Stage 3**.

Sem um modelo claro de runtime dedicado, **não existe Enterprise Ready no CONTRACTOR**.

---
