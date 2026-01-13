# 📘 ADR 0030 — **Bundle Marketplace Governance Model**

**Status:** Draft
**Date:** 2026-01-13
**Stage:** 4 — Platform Ecosystem
**Related:**

* ADR 0021 — Product Roadmap and Maturity Stages
* ADR 0029 — Stage 4 Platform Ecosystem Vision

---

## Context

No Stage 4, o CONTRACTOR passa a operar como uma **plataforma extensível**, onde bundles podem ser:

* criados por terceiros
* distribuídos entre tenants
* reutilizados como blocos de valor

Sem um modelo explícito de governança, um marketplace de bundles introduz riscos críticos:

* quebra de isolamento
* degradação de qualidade
* insegurança operacional
* fragmentação do ecossistema

Portanto, **marketplace não pode ser sinônimo de abertura irrestrita**.
É necessário um **modelo formal de governança** antes de qualquer execução.

---

## Decision

Adotar um **Bundle Marketplace com governança rígida**, baseado em:

* curadoria explícita
* contratos claros
* quality gates obrigatórios
* separação entre autoria, publicação e consumo

Este ADR define **as regras do jogo**, não a implementação técnica.

---

## Definição de Bundle no Marketplace

Um bundle de marketplace é:

* um **artefato versionado e imutável**
* composto por ontologia, entities, policies, templates e suites
* validado por contratos formais
* executado **exclusivamente** pelo runtime do CONTRACTOR

Nenhum bundle pode executar código fora do sandbox definido pelo runtime.

---

## Papéis no Marketplace

### 1. Bundle Author

* Cria e versiona bundles
* Responsável pela compatibilidade semântica
* Não tem acesso direto a dados de tenants

---

### 2. Bundle Publisher

* Submete bundles ao marketplace
* Declara metadados, dependências e compatibilidade
* Aceita termos de governança e responsabilidade

> Em alguns casos, Author e Publisher podem ser o mesmo ator.

---

### 3. Bundle Consumer (Tenant)

* Opta explicitamente por consumir bundles
* Controla versões e promoções via aliases
* Pode desabilitar ou remover bundles a qualquer momento

---

### 4. Platform Operator

* Define políticas globais
* Opera a curadoria
* Aplica sanções (ex.: delist)
* Garante compliance do ecossistema

---

## Curadoria e Classificação

Todo bundle publicado deve conter:

* **categoria** (ex.: analytics, finance, ops)
* **nível de maturidade** (experimental / stable / certified)
* **escopo de dados**
* **impacto operacional esperado**

Bundles não certificados **não podem** ser promovidos automaticamente para `current`.

---

## Quality Gates Obrigatórios

Antes da publicação:

* validação de schema
* validação de ontologia
* execução de suites mínimas
* verificação de políticas proibidas
* análise de impacto operacional

Após publicação:

* monitoramento de falhas
* métricas por bundle
* feedback loop de qualidade

---

## Versionamento e Compatibilidade

* Versionamento **semântico obrigatório**
* Breaking changes exigem major bump
* Compatibilidade declarada explicitamente
* Depreciação deve seguir janela mínima definida pela plataforma

---

## Segurança e Isolamento

* Bundles não compartilham estado
* Nenhum acesso direto a secrets
* Nenhum acesso direto a dados cross-tenant
* Todo acesso passa pelo runtime e policies ativas

---

## Delisting e Sanções

A plataforma pode:

* deslistar bundles problemáticos
* bloquear versões específicas
* forçar rollback em casos críticos
* revogar acesso de publishers reincidentes

Todos os eventos devem ser auditáveis.

---

## Explicit Non-Goals

Este ADR **não cobre**:

* modelo comercial
* precificação
* revenue sharing
* contratos legais com parceiros
* APIs públicas de marketplace

Esses tópicos exigem ADRs próprios.

---

## Entry Criteria

O Bundle Marketplace **só pode ser ativado** se:

* ADR 0029 estiver **Accepted**
* Pelo menos um tenant enterprise ativo
* Operação Stage 3 estável
* Ferramentas mínimas de curadoria disponíveis

---

## Consequences

* O ecossistema cresce com controle
* A plataforma mantém previsibilidade
* A confiança entre tenants é preservada
* O CONTRACTOR se torna defensável como plataforma

---

## Final Statement

> **Marketplace não é abertura — é governança em escala.**

Este ADR estabelece as bases do marketplace do CONTRACTOR.
Qualquer automação futura exigirá novos ADRs.

---
