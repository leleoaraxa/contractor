# 📘 ADR 0038 — **Platform Exit, Sunset & Ecosystem Decommissioning Model**

**Status:** Draft
**Date:** 2026-01-13
**Stage:** Cross-Stage (aplica-se a Stage 2, 3 e 4)

**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0029 — Stage 4 Platform Ecosystem Vision
* ADR 0037 — Marketplace Quality Enforcement & Bundle Lifecycle
* ADR 0018 — Data Privacy, LGPD/GDPR and Retention Policies

---

## Context

Plataformas maduras precisam planejar **não apenas como crescer**, mas **como encerrar ciclos com segurança, previsibilidade e responsabilidade**.

Sem um modelo explícito de exit e sunset, o CONTRACTOR estaria sujeito a:

* encerramentos improvisados
* risco legal e reputacional
* perda de confiança de tenants e parceiros
* dados órfãos e artefatos sem governança
* dependências quebradas sem aviso

Um **modelo formal de encerramento** é requisito de plataformas enterprise-grade.

---

## Decision

Adotar um **Platform Exit & Decommissioning Model** explícito, documentado e auditável, cobrindo:

* sunset de funcionalidades
* encerramento de bundles
* saída de tenants
* descontinuação parcial ou total da plataforma
* preservação de evidências e obrigações legais

O encerramento passa a ser tratado como **capacidade de produto**, não como exceção.

---

## Princípios

1. **No silent shutdowns**
2. **Predictability over speed**
3. **Data dignity**
4. **Auditability by design**
5. **Exit is part of the contract**

---

## Tipos de Encerramento

### 1) Feature Sunset

* Funcionalidade específica descontinuada
* Mantida em modo compatibilidade por período definido
* Comunicação antecipada obrigatória

---

### 2) Bundle Sunset

* Bundle entra em estado `Deprecated` → `Retired`
* Janelas de migração explícitas
* Evidência preservada (ADR 0037)

---

### 3) Tenant Exit

* Tenant solicita encerramento de contrato
* Plataforma executa:

  * desligamento controlado
  * purge conforme policies
  * entrega de evidências/export (quando aplicável)

---

### 4) Partial Platform Decommission

* Descontinuação de:

  * regiões
  * planos
  * segmentos de mercado
* Migração assistida ou encerramento negociado

---

### 5) Full Platform Sunset

* Encerramento completo do CONTRACTOR
* Raro, mas explicitamente planejado

---

## Sunset Lifecycle

Todo encerramento segue o mesmo ciclo:

1. **Announcement**

   * Comunicação formal
   * Datas, escopo e impactos claros

2. **Stabilization**

   * Congelamento de novas adoções
   * Correções críticas apenas

3. **Migration / Exit Window**

   * Tempo suficiente para adaptação
   * Ferramentas e documentação disponíveis

4. **Execution**

   * Desligamento conforme plano
   * Preservação de evidências

5. **Closure**

   * Auditoria final
   * Registro histórico

---

## Data Handling & Compliance

Durante qualquer exit:

* Retenção segue ADR 0018
* Dados de domínio:

  * nunca apropriados pela plataforma
  * eliminados conforme policy
* Metadados:

  * mantidos pelo período legal mínimo
* Evidências:

  * preservadas para auditoria

---

## Comunicação Obrigatória

Toda ação de sunset exige:

* comunicação escrita
* antecedência mínima definida por estágio
* registro em audit log
* versão pública da política de sunset

---

## Responsabilidades

* **Platform Owner**

  * define estratégia e cronograma
* **Legal / Compliance**

  * valida obrigações regulatórias
* **Engineering**

  * executa o plano técnico
* **Partners**

  * cooperam em bundles e migrações

---

## Explicit Non-Goals

Este ADR **não define**:

* valores de compensação
* termos comerciais específicos
* renegociação contratual
* detalhes jurídicos por jurisdição

Esses itens são tratados fora do escopo técnico.

---

## Entry Criteria

Este ADR se aplica quando o CONTRACTOR atinge:

* Stage 2 (Production Ready) ou superior
* compromissos comerciais ativos
* parceiros externos ou marketplace

---

## Consequences

* Redução drástica de risco legal
* Confiança institucional aumentada
* Encerramentos previsíveis e defensáveis
* Plataforma percebida como madura e responsável

---

## Final Statement

> **A platform that cannot exit responsibly was never truly enterprise-ready.**

Este ADR encerra o ciclo completo do CONTRACTOR — da fundação ao encerramento — de forma explícita, ética e sustentável.

---

## ✅ Encerramento do Arco ADR

Com o **ADR 0038**, o CONTRACTOR possui agora:

* Roadmap completo (Stage 0 → Stage 4)
* Governança técnica, comercial e legal
* Ecossistema com lifecycle disciplinado
* Plano explícito de encerramento

