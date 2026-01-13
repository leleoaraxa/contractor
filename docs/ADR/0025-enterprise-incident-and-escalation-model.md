# 📘 ADR 0025 — **Enterprise Incident & Escalation Model**

**Status:** Draft
**Date:** 2026-01-13
**Stage:** 3 — Enterprise Ready
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0022 — Dedicated Runtime & Isolation Model
* ADR 0023 — Enterprise SLA Model
* ADR 0024 — Tenant-Level Observability
* ADR 0018 — Data Privacy, LGPD/GDPR and Retention Policies

---

## Context

No Stage 3, o CONTRACTOR passa a operar com:

* **runtimes dedicados por tenant**
* **SLAs contratuais explícitos**
* **observabilidade isolada e auditável**

Nesse contexto, incidentes deixam de ser apenas eventos técnicos e passam a ser **eventos contratuais**, com impacto direto em:

* SLA
* confiança do cliente
* obrigações legais e comerciais

É necessário definir um **modelo formal de incidentes e escalonamento**, adequado a clientes enterprise, sem assumir complexidades desnecessárias antes da hora.

---

## Decision

Adotar um **Enterprise Incident & Escalation Model**, com:

* classificação clara de severidade
* gatilhos objetivos baseados em métricas
* responsabilidades bem definidas
* integração direta com SLA e observabilidade

O modelo é **obrigatório para Stage 3** e **inexistente no Stage 2**.

---

## Incident Principles

1. **Incidents are contractual events**
2. **Metrics define severity**
3. **Escalation is predictable**
4. **No silent failures**
5. **Postmortem is mandatory**

---

## Incident Definition

Um incidente enterprise é qualquer evento que resulte em:

* violação ou risco real de violação de SLA
* indisponibilidade parcial ou total do runtime dedicado
* degradação mensurável acima dos thresholds contratuais
* falha operacional que impeça o uso normal do serviço

---

## Severity Levels (Enterprise)

| Severidade | Definição                                        | Impacto |
| ---------- | ------------------------------------------------ | ------- |
| **SEV-1**  | Serviço indisponível ou SLA em violação imediata | Crítico |
| **SEV-2**  | Degradação relevante com risco de SLA            | Alto    |
| **SEV-3**  | Degradação limitada, sem risco imediato          | Médio   |
| **SEV-4**  | Evento informativo / operacional                 | Baixo   |

---

## Incident Triggers

### 1. Automatic Triggers (Preferred)

Baseados em métricas tenant-level (ADR 0024):

* disponibilidade abaixo do target
* latência acima do limite contratual
* error rate sustentado
* saturação crítica de recursos

---

### 2. Manual Triggers

* reporte do cliente enterprise
* detecção por operação
* falhas de dependências externas

---

## Escalation Model

### 1. Escalation Flow

1. **Detection**
2. **Classification (SEV)**
3. **Notification**
4. **Mitigation**
5. **Resolution**
6. **Postmortem**
7. **SLA Accounting**

---

### 2. Escalation Matrix (Stage 3)

| Severidade | Comunicação | SLA Clock |
| ---------- | ----------- | --------- |
| SEV-1      | Imediata    | Sim       |
| SEV-2      | Até 30 min  | Sim       |
| SEV-3      | Até 4h      | Não       |
| SEV-4      | Best effort | Não       |

---

## Communication Model

### 1. Internal Communication

* operação
* engenharia
* liderança técnica

---

### 2. Customer Communication (Enterprise)

* status inicial
* updates periódicos
* encerramento formal
* relatório pós-incidente

---

## Mitigation & Resolution

* rollback de bundle (ADR 0022)
* isolamento de runtime
* redução de carga
* correções emergenciais

Mitigação **sempre precede** análise de causa raiz.

---

## Postmortem Policy

### Mandatory Postmortem for:

* todos os SEV-1
* SEV-2 com impacto mensurável

Postmortem deve conter:

* linha do tempo
* impacto
* causa raiz
* ações corretivas
* evidências métricas

---

## SLA Integration

* Incidentes alimentam:

  * cálculo de SLA
  * créditos contratuais (ADR 0023)
* Métricas usadas são:

  * tenant-level
  * imutáveis após fechamento

---

## Roles & Responsibilities

| Papel      | Responsabilidade          |
| ---------- | ------------------------- |
| Operação   | detecção e mitigação      |
| Engenharia | correção definitiva       |
| Produto    | comunicação e alinhamento |
| Comercial  | interface contratual      |

---

## Privacy & Compliance

* Total alinhamento com ADR 0018
* Nenhum payload sensível em:

  * relatórios
  * postmortems
  * comunicações externas

---

## Alternatives Considered

### 1) Incident handling ad hoc

**Cons:** imprevisível, não defensável.

---

### 2) Full ITIL / NOC complex

**Cons:** overkill para Stage 3.

---

### 3) **Contract-driven incident model (chosen)**

**Pros:**

* claro
* auditável
* escalável
* alinhado a SLA

---

## Consequences

* Redução de disputas contratuais
* Aumento de confiança enterprise
* Engenharia menos reativa
* Operação previsível

---

## Explicit Non-Goals

Este ADR **não define**:

* suporte 24x7 global
* multi-region DR automático
* incident tooling avançado (PagerDuty, Opsgenie)
* processos regulatórios formais (SOC2/ISO)

Esses itens pertencem ao **Stage 4**.

---

## Final Notes

Sem um modelo formal de incidentes, **SLA é apenas marketing**.

Este ADR fecha o **ciclo operacional do Stage 3**:

* isolamento
* observabilidade
* SLA
* incidentes

---
