# 📘 ADR 0007 — **Security Baseline and Threat Model**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0007 — Security Baseline and Threat Model**

## Context

CONTRACTOR processa:

* contratos sensíveis
* queries reais em dados de clientes
* credenciais de acesso
* respostas potencialmente estratégicas

A plataforma deve ser **secure by default**, inclusive no MVP, sem depender de “endurecimento futuro”.

## Decision

Adotar um **Security Baseline mínimo obrigatório**, acompanhado de um **Threat Model explícito**, versionado e auditável.

## Security Baseline (v0)

### Identity & Access

* Autenticação obrigatória em todos os planos
* RBAC mínimo:

  * platform_admin
  * tenant_admin
  * tenant_editor
  * tenant_viewer
* Runtime **não** executa ações administrativas

### Secrets Management

* Segredos **nunca** armazenados em config files
* Uso obrigatório de:

  * AWS Secrets Manager (ou equivalente)
  * KMS para encryption-at-rest
* Runtime acessa segredos apenas em memória

### Network Security

* TLS obrigatório (control plane ↔ runtime ↔ datasources)
* Runtime exposto apenas via gateway
* Para Agent:

  * mTLS
  * outbound-only from client environment

### Data Handling

* Proibição de persistência de dados do cliente
* Cache é:

  * efêmero
  * segregado por tenant
  * com TTL explícito
* Logs e traces passam por redaction obrigatória

### Template & Execution Safety

* Templates executados em sandbox
* Allowlist explícita de filtros e funções
* Nenhuma forma de execução arbitrária (eval, exec)

## Threat Model (initial)

### Threats Considered

* Cross-tenant data leakage
* Credential exfiltration
* Injection via templates or SQL parameters
* Privilege escalation (editor → admin)
* Observability leakage (logs/traces)
* Malicious ontology or template uploads

### Mitigations

* Tenant isolation rules (ADR 0003)
* Read-only DB access
* SQL parameterization only
* Static + dynamic validation of artifacts
* Redaction layer mandatory
* Audit log for all promotions and changes

## Alternatives Considered

### 1) Harden later (common MVP shortcut)

**Cons:** security debt, retrabalho, risco comercial.

### 2) Zero-trust full enterprise from day one

**Cons:** inviável para MVP, custo alto.

### 3) **Baseline + extensible threat model (chosen)**

**Pros:** segurança realista, evolutiva e auditável.

## Implications

* Todo PR deve declarar impacto em segurança (sim/não)
* Threat model é documento vivo (`docs/SECURITY/threat-model.md`)
* Qualquer nova feature:

  * ou se encaixa no baseline
  * ou exige novo ADR

## Consequences

Segurança deixa de ser implícita e passa a ser **parte do contrato do produto**, aumentando confiança de clientes enterprise desde cedo.

---
