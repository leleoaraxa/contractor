# 📘 ADR 0018 — **Data Privacy, LGPD/GDPR and Retention Policies**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0018 — Data Privacy, LGPD/GDPR and Retention Policies**

## Context

O CONTRACTOR processa dados de clientes em múltiplos níveis:

* metadados operacionais (tenants, bundles, métricas)
* dados transitórios de execução (rows em memória, cache efêmero)
* logs, métricas e traces
* possíveis dados pessoais (PII) dependendo do domínio do tenant

Para viabilizar uso comercial e enterprise, a plataforma deve ser **privacy-by-design** e **privacy-by-default**, atendendo LGPD e GDPR sem depender de acordos ad hoc.

## Decision

Adotar um **modelo explícito de privacidade, classificação de dados e retenção**, controlado por policy, com **mínima persistência** e **direitos do titular suportados por design**.

### Princípios

1. **Data minimization**
2. **Purpose limitation**
3. **Ephemeral processing by default**
4. **Tenant responsibility for domain PII**

## Data Classification Model

### Data Classes

* **Class A — Platform Metadata**

  * tenants, bundles, versions, audit logs
* **Class B — Operational Telemetry**

  * métricas agregadas
  * logs redigidos
  * traces sem payload sensível
* **Class C — Transient Execution Data**

  * rows em memória
  * cache runtime
* **Class D — Customer Domain Data (PII-capable)**

  * dados retornados via SQL
  * nunca persistidos pela plataforma

## Retention Policies

### Default Retention

* Class A: conforme requisitos legais/comerciais (ex.: 2–5 anos)
* Class B: curto prazo (ex.: 7–30 dias), configurável por tenant/plano
* Class C: **somente em memória ou cache efêmero** (TTL obrigatório)
* Class D: **zero retention** (process-only)

Nenhuma classe pode ter retenção “infinita”.

### Policy-Driven Overrides

* Retenção pode ser ajustada:

  * por tenant
  * por ambiente
  * por plano
* Overrides exigem registro em audit log.

## LGPD/GDPR Responsibilities

### Role Definition

* CONTRACTOR atua como **Data Processor**.
* Tenant atua como **Data Controller** dos dados de domínio.

### Supported Rights

A plataforma deve permitir:

* direito de acesso (transparência operacional)
* direito de exclusão (deleção de metadados e telemetria associada)
* direito de restrição (desabilitar logging/tracing)
* portabilidade de metadados (export de bundles e configs)

### Explicit Non-Responsibilities

* CONTRACTOR **não**:

  * classifica PII de domínio automaticamente
  * armazena dados pessoais de clientes
  * realiza anonimização de dados de domínio

## Alternatives Considered

### 1) Persistir dados para debug

**Cons:** alto risco legal; inviável enterprise.

### 2) Delegar tudo ao cliente

**Cons:** produto fraco; risco de não conformidade.

### 3) **Privacy-by-design com policies (chosen)**

**Pros:** compliance forte; previsibilidade; escalabilidade.

## Implications

* Redaction layer obrigatória em logs/traces
* Retention configurável como policy
* Documentação clara de papéis (DPA)
* Testes de privacidade como parte da quality suite

## Consequences

A plataforma nasce **compliance-ready**, reduzindo barreiras legais e acelerando vendas enterprise.

---
