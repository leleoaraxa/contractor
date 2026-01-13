# 📘 ADR 0026 — **Enterprise Data Residency & Compliance Boundaries**

**Status:** Draft
**Date:** 2026-01-13
**Stage:** 3 — Enterprise Ready
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0022 — Dedicated Runtime & Isolation Model
* ADR 0023 — Enterprise SLA Model
* ADR 0024 — Tenant-Level Observability
* ADR 0025 — Enterprise Incident & Escalation Model
* ADR 0018 — Data Privacy, LGPD/GDPR and Retention Policies

---

## Context

Com o avanço para o **Stage 3 (Enterprise Ready)**, o CONTRACTOR passa a atender clientes sujeitos a:

* LGPD (Brasil)
* GDPR (União Europeia)
* requisitos internos de compliance corporativo
* políticas de localização de dados (data residency)

Esses clientes exigem **clareza absoluta sobre onde dados podem existir, circular e ser processados**, mesmo quando a plataforma não persiste dados de domínio.

Sem limites explícitos, surgem riscos de:

* promessas implícitas não sustentáveis
* violações contratuais
* bloqueios comerciais desnecessários
* confusão entre *processamento transitório* e *armazenamento*

---

## Decision

Definir um **modelo explícito de Data Residency & Compliance Boundaries**, no qual:

* os **limites de responsabilidade da plataforma** são claros
* o que é **configurável por tenant** é explicitado
* o que **não é suportado no Stage 3** é declarado sem ambiguidade

O objetivo não é “compliance total”, mas **compliance defensável e honesto**.

---

## Core Principles

1. **Boundaries over promises**
2. **Processing ≠ Storage**
3. **Residency applies to persisted data**
4. **Tenant controls domain data**
5. **No silent assumptions**

---

## Data Residency Model (Stage 3)

### 1. What Data Residency Applies To

Data residency no CONTRACTOR **aplica-se somente a dados persistidos**, incluindo:

* artefatos de runtime (bundles, manifests)
* audit logs
* métricas agregadas
* logs operacionais

**Não se aplica** a:

* dados transitórios em memória
* payloads processados apenas durante execução
* dados de domínio retornados por SQL

---

## Residency Scope by Data Class

| Classe (ADR 0018)                      | Residency Guarantee                        |
| -------------------------------------- | ------------------------------------------ |
| **Class A — Platform Metadata**        | Região configurada por tenant              |
| **Class B — Operational Telemetry**    | Região configurada por tenant              |
| **Class C — Transient Execution Data** | Sem garantia (processamento efêmero)       |
| **Class D — Customer Domain Data**     | Zero retention; responsabilidade do tenant |

---

## Supported Residency Options (Stage 3)

Para tenants enterprise, o CONTRACTOR pode oferecer:

* seleção de **região primária** do runtime dedicado
* persistência de:

  * bundles
  * audit logs
  * métricas
  * logs
    **dentro da região escolhida**

Exemplos (não exaustivos):

* `sa-east-1` (Brasil)
* `us-east-1`
* `eu-west-1`

---

## Explicit Non-Guarantees

No Stage 3, o CONTRACTOR **não garante**:

* processamento exclusivamente local (in-memory) por região
* zero-cross-region network traffic
* controle sobre:

  * backbone de cloud provider
  * roteamento de pacotes
* residência para dados **não persistidos**

Esses limites são **documentados e contratuais**.

---

## Compliance Boundaries

### 1. CONTRACTOR Responsibilities

CONTRACTOR atua como **Data Processor** e garante:

* isolamento por tenant (ADR 0022)
* observabilidade segregada (ADR 0024)
* retenção configurável (ADR 0018)
* evidências de SLA e incidentes (ADR 0023 / 0025)

---

### 2. Tenant Responsibilities

O tenant atua como **Data Controller** e é responsável por:

* classificação de PII de domínio
* decisões de onde dados de domínio residem
* conformidade regulatória específica do seu setor
* uso apropriado da plataforma

---

## Audit & Evidence

Para clientes enterprise, a plataforma pode fornecer:

* documentação de arquitetura
* descrição formal dos fluxos de dados
* evidência de localização de dados persistidos
* relatórios de incidentes e SLA

**Não fornece** auditorias regulatórias completas (SOC2/ISO).

---

## Contractual Language

Contratos enterprise devem:

* referenciar explicitamente este ADR
* declarar:

  * o que é garantido
  * o que não é garantido
* evitar termos vagos como:

  * “full compliance”
  * “complete data residency”

---

## Alternatives Considered

### 1) Prometer full data residency

**Cons:** tecnicamente indefensável; risco legal.

---

### 2) Ignorar residency até Stage 4

**Cons:** bloqueia vendas enterprise.

---

### 3) **Explicit boundaries model (chosen)**

**Pros:**

* honesto
* defensável
* comercialmente viável
* escalável

---

## Consequences

* Menos risco legal
* Expectativas claras
* Vendas enterprise desbloqueadas
* Engenharia protegida de promessas irreais

---

## Explicit Non-Goals

Este ADR **não define**:

* multi-region active-active
* sovereign cloud
* air-gapped environments
* certificações regulatórias formais

Esses itens pertencem ao **Stage 4+**.

---

## Final Notes

Compliance não é um “estado mágico”, é um **conjunto de limites claros**.

Este ADR fecha o **perímetro de responsabilidade do Stage 3**, permitindo:

* contratos enterprise sustentáveis
* evolução consciente para Stage 4
* zero surpresa operacional ou legal

---
