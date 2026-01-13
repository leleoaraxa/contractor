# 📘 ADR 0034 — **Marketplace Legal, Tax & Jurisdiction Abstraction**

**Status:** Draft
**Date:** 2026-01-13
**Stage:** 4 — Platform Ecosystem
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0029 — Stage 4 Platform Ecosystem Vision
* ADR 0030 — Bundle Marketplace Governance Model
* ADR 0032 — Marketplace Commercial & Revenue Model
* ADR 0033 — Marketplace Billing, Invoicing & Financial Reconciliation

---

## Context

Com o **billing técnico e a reconciliação financeira** definidos (ADR 0033), o CONTRACTOR entra em um domínio inevitável:

* diferentes países
* diferentes regimes fiscais
* diferentes responsabilidades legais
* diferentes papéis contratuais (platform, partner, tenant)

Misturar **lógica legal/fiscal** com **engenharia de billing** cria:

* código frágil
* dívida regulatória
* risco jurídico sistêmico
* impossibilidade de operar globalmente

É necessário um **modelo explícito de abstração legal e fiscal**, desacoplado do core técnico.

---

## Decision

Adotar um **Legal, Tax & Jurisdiction Abstraction Model**, onde:

* o core da plataforma permanece **jurisdiction-agnostic**
* regras legais e fiscais são **configuradas, não codificadas**
* responsabilidades são explicitamente declaradas
* a plataforma atua como **infraestrutura técnica**, não como autoridade fiscal

---

## Princípios

1. **Engineering is global, law is local**
2. **No legal logic in the runtime**
3. **Tax rules are policies, not code**
4. **Explicit responsibility beats implicit liability**
5. **Abstraction first, specialization later**

---

## Modelo de Papéis Legais

### Entidades Envolvidas

* **Platform Operator**
  Operador do CONTRACTOR (ex.: SIRIOS / white-label owner)

* **Partner / Integrator**
  Fornecedor de bundles, extensões ou serviços

* **Tenant / Customer**
  Consumidor final da plataforma

---

### Papéis Legais

| Papel    | Responsabilidade                                             |
| -------- | ------------------------------------------------------------ |
| Platform | Infraestrutura técnica, billing técnico, metering            |
| Partner  | Conteúdo, bundle, licenciamento, obrigações fiscais próprias |
| Tenant   | Uso final, dados de domínio, obrigações locais               |

A plataforma **não assume automaticamente** obrigações fiscais do partner ou tenant.

---

## Abstração de Jurisdição

A plataforma introduz o conceito de:

```
jurisdiction_profile
```

Associado a:

* tenant
* partner
* transação (quando aplicável)

Este perfil define:

* país/região
* regime fiscal aplicável
* exigências legais específicas

---

## Tax Abstraction Layer

O CONTRACTOR **não calcula impostos no core**.

Em vez disso:

* o billing engine gera **valores brutos**
* uma **tax abstraction layer** define:

  * se imposto se aplica
  * quem é responsável
  * como deve ser apresentado

Essa camada é:

* declarativa
* versionada
* auditável
* substituível por integrações externas

---

## Invoicing & Legal Representation

Invoices e statements podem ser emitidos como:

* **Technical Invoice** (default)
* **Legal Invoice** (via integração externa)

O core gera:

* uso
* valores
* splits

A conformidade legal ocorre:

* fora do runtime
* fora do billing core

---

## Compliance Boundaries

Este ADR **define limites claros**:

### A plataforma NÃO:

* calcula impostos automaticamente
* determina alíquotas locais
* garante compliance fiscal global
* atua como substituto tributário sem contrato explícito

### A plataforma SUPORTA:

* export de dados fiscais
* trilhas de auditoria
* integração com ERPs e fiscal engines
* múltiplos regimes por tenant/partner

---

## Auditoria Legal

* Todo billing é rastreável a eventos técnicos
* Toda transformação legal é versionada
* Diferenças entre bruto e líquido são explícitas

Não existem:

* ajustes ocultos
* regras implícitas
* exceções silenciosas

---

## Entry Criteria

Este modelo é ativado quando:

* marketplace opera multi-jurisdição
* partners globais existem
* billing técnico está estável
* necessidade legal ultrapassa o país de origem

---

## Consequences

* Core técnico permanece simples e escalável
* Compliance pode evoluir sem refatorar runtime
* Menor risco jurídico sistêmico
* Pronto para expansão internacional

---

## Explicit Non-Goals

Este ADR **não define**:

* regimes fiscais específicos (VAT, ICMS, GST etc.)
* contratos legais
* documentos fiscais oficiais
* gateways de pagamento
* obrigações contábeis locais

Esses temas exigem ADRs legais e financeiros específicos.

---

## Final Statement

> **Legal complexity must surround the platform — never infect it.**

Este ADR garante que o CONTRACTOR possa operar globalmente sem sacrificar a integridade do seu core técnico.

---
