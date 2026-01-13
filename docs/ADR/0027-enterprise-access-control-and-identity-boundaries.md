# 📘 ADR 0027 — **Enterprise Access Control & Identity Boundaries**

**Status:** Draft
**Date:** 2026-01-13
**Stage:** 3 — Enterprise Ready
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0022 — Dedicated Runtime & Isolation Model
* ADR 0023 — Enterprise SLA Model
* ADR 0024 — Tenant-Level Observability
* ADR 0025 — Enterprise Incident & Escalation Model
* ADR 0026 — Enterprise Data Residency & Compliance Boundaries
* ADR 0018 — Data Privacy, LGPD/GDPR and Retention Policies

---

## Context

Com runtimes dedicados, SLAs contratuais, observabilidade por tenant e limites claros de compliance, o último pilar estrutural do **Stage 3 (Enterprise Ready)** é o **controle explícito de identidade e acesso**.

No Stage 2, o acesso é:

* baseado em API keys
* orientado a uso técnico
* suficiente para SMB/Pro

Para clientes enterprise, isso é insuficiente. É necessário definir **fronteiras claras de quem pode fazer o quê**, **em qual escopo**, e **com qual nível de responsabilidade**, sem introduzir complexidade de IAM excessiva antes do tempo.

---

## Decision

Adotar um **Enterprise Access Control & Identity Boundaries Model**, no qual:

* identidade e acesso são **explícitos por papel**
* escopos são **limitados por tenant**
* credenciais são **segregadas por finalidade**
* integrações enterprise são **possíveis, mas não obrigatórias**

O modelo é **obrigatório para Stage 3** e **não existe no Stage 2**.

---

## Access Control Principles

1. **Explicit is better than implicit**
2. **Least privilege by default**
3. **Identity ≠ Runtime**
4. **Tenant boundary is absolute**
5. **No shared credentials**

---

## Identity Model (Stage 3)

### 1. Identity Types

O CONTRACTOR reconhece os seguintes tipos de identidade:

| Tipo                  | Descrição                                               |
| --------------------- | ------------------------------------------------------- |
| **Service Identity**  | Identidade usada por aplicações/serviços clientes       |
| **Operator Identity** | Identidade de operadores humanos (tenant ou CONTRACTOR) |
| **Platform Identity** | Identidade interna da plataforma                        |

---

## Authentication Mechanisms

### 2. Supported Mechanisms

No Stage 3, são suportados:

* **API Keys segregadas por escopo**
* **Rotação manual de credenciais**
* **Revogação imediata**

Integrações opcionais (não obrigatórias):

* SSO corporativo
* Identity Providers externos

---

## Authorization Model

### 3. Role-Based Access Control (RBAC)

O modelo de autorização é **RBAC simples**, com papéis fixos e bem definidos.

#### Papéis Canônicos

| Papel                     | Escopo     | Permissões                                     |
| ------------------------- | ---------- | ---------------------------------------------- |
| **Tenant Runtime Client** | Runtime    | Executar `/ask`                                |
| **Tenant Operator**       | Tenant     | Gerenciar aliases, observar métricas agregadas |
| **Tenant Admin**          | Tenant     | Gerenciar identidades do tenant                |
| **CONTRACTOR Operator**   | Plataforma | Operação e incidentes                          |
| **CONTRACTOR Admin**      | Plataforma | Acesso administrativo restrito                 |

---

## Scope Boundaries

### 4. Tenant Isolation

* Toda identidade é **associada a um único tenant**
* Não existe:

  * identidade cross-tenant
  * chave global multi-tenant
* Escopos são sempre:

  ```
  <tenant_id> : <role> : <capability>
  ```

---

## Credential Management

### 5. Credential Lifecycle (Stage 3)

* Criação: manual, auditada
* Rotação: manual, documentada
* Revogação: imediata
* Auditoria: obrigatória (audit log)

Nenhuma credencial é:

* compartilhada entre tenants
* reaproveitada entre ambientes
* gerada automaticamente sem registro

---

## Audit & Traceability

* Todas as ações sensíveis geram:

  * audit log
  * timestamp
  * identity_id
  * tenant_id
* Logs de auditoria:

  * não contêm payload
  * respeitam retenção (ADR 0018)

---

## Incident & Access

Durante incidentes (ADR 0025):

* acessos emergenciais:

  * são temporários
  * são auditados
  * são revogados após o incidente
* nenhuma exceção permanente é criada

---

## Privacy & Compliance

* Total alinhamento com ADR 0018
* CONTRACTOR atua como **Data Processor**
* Identidade:

  * não armazena PII desnecessário
  * não expõe dados cross-tenant

---

## Explicit Non-Goals

Este ADR **não define**:

* IAM granular dinâmico
* políticas ABAC complexas
* gestão automática de usuários finais
* federação obrigatória de identidade
* MFA obrigatório

Esses itens pertencem ao **Stage 4+**.

---

## Alternatives Considered

### 1) IAM complexo desde o início

**Cons:** alto custo, baixa adoção, risco de overengineering.

---

### 2) Manter API keys simples

**Cons:** insuficiente para enterprise.

---

### 3) **RBAC explícito e limitado (chosen)**

**Pros:**

* simples
* auditável
* enterprise-ready
* evolutivo

---

## Consequences

* Limites claros de acesso
* Menor risco de vazamento
* Operação previsível
* Base sólida para Stage 4

---

## Final Notes

Sem fronteiras claras de identidade e acesso, **isolamento e SLA não se sustentam**.

Este ADR fecha **todos os pilares do Stage 3**:

* runtime dedicado
* observabilidade
* SLA
* incidentes
* compliance
* identidade

A partir daqui, qualquer avanço é **escala, automação ou ecossistema**.

---
