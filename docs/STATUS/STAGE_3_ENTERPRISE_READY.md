# 📘 STAGE 3 — Enterprise Ready

**Status:** Draft (Status Document)
**Relacionado:** ADR 0021 — Product Roadmap and Maturity Stages
**Última atualização:** 2026-01-XX

---

## 1. Purpose

Este documento define **o significado exato de “Enterprise Ready”** no contexto do CONTRACTOR.

Ele **não** descreve arquitetura detalhada, **não** decide implementações técnicas específicas e **não** substitui ADRs.
Seu papel é estabelecer **o contrato de maturidade do Stage 3**, servindo como referência obrigatória para:

* decisões arquiteturais futuras
* criação de ADRs do Stage 3
* comunicação comercial e de vendas
* alinhamento entre produto, engenharia e operações

Nenhuma capability enterprise pode ser anunciada, vendida ou implementada sem aderência a este documento.

---

## 2. Definition of Enterprise Ready

Um sistema **Enterprise Ready** no CONTRACTOR é aquele que:

* oferece **isolamento forte e previsível por tenant**
* suporta **compromissos operacionais contratuais (SLAs)**
* atende requisitos formais de **compliance, auditoria e governança**
* permite **controle operacional explícito** por clientes enterprise
* mantém **determinismo e reversibilidade** mesmo sob falhas

Enterprise Ready **não significa** escala máxima, marketplace ou automação total — esses pertencem ao Stage 4.

---

## 3. Entry Criteria (Pré-requisitos obrigatórios)

O Stage 3 **só pode iniciar** se **todos** os critérios abaixo estiverem atendidos:

### 3.1 Maturidade do Stage 2 (obrigatório)

* SLOs ativos e monitorados
* Incident Management documentado e operacional
* Rollback completo e validado
* SDKs estáveis e versionados
* Políticas explícitas de privacidade e retenção (ADR 0018)

> Stage 3 **não corrige lacunas do Stage 2**.

---

### 3.2 Estabilidade arquitetural

* Runtime e Control Plane com contratos estáveis
* Bundles e aliases totalmente imutáveis
* Nenhuma dependência crítica “experimental” em produção

---

## 4. Core Capabilities — Stage 3

### 4.1 Runtime & Isolation

* Runtime **dedicado ou logicamente isolado por tenant**
* Garantias explícitas de:

  * isolamento de carga
  * isolamento de falhas
  * previsibilidade de latência
* Nenhum tenant pode degradar outro

> O **modelo exato de isolamento** será definido por ADR específico.

---

### 4.2 Security & Access Control

* Gestão de credenciais por tenant
* Rotação de chaves e segregação de acessos
* Controles explícitos de:

  * quem pode operar
  * quem pode auditar
  * quem pode promover bundles

---

### 4.3 Compliance & Auditability

* Audit logs completos, estruturados e imutáveis
* Rastreabilidade clara entre:

  * ações operacionais
  * bundles
  * decisões de runtime
* Suporte a auditorias externas (ex.: SOC2-like, ISO-like)

> O CONTRACTOR continua atuando como **Data Processor**.

---

### 4.4 SLAs & Operação Enterprise

* Definição formal de SLAs:

  * disponibilidade
  * tempo de resposta
  * suporte
* Procedimentos claros de:

  * escalonamento
  * comunicação de incidentes
  * relatórios pós-incidente

---

### 4.5 Observability Avançada

* Métricas por tenant
* Logs com níveis configuráveis
* Tracing **opcional** e sem payload sensível
* Capacidade de exportar dados operacionais para sistemas do cliente

---

## 5. Explicit Non-Goals (fora do Stage 3)

O Stage 3 **não inclui**:

* Marketplace de bundles
* Automação completa de rollout (canary, A/B avançado)
* Billing sofisticado multi-dimensional
* Data residency multi-região automática
* Customizações profundas por cliente sem governança

Esses itens pertencem ao **Stage 4 — Platform Ecosystem**.

---

## 6. What Changes vs Stage 2

| Dimensão    | Stage 2       | Stage 3            |
| ----------- | ------------- | ------------------ |
| Runtime     | Compartilhado | Dedicado / Isolado |
| SLO         | Interno       | Contratual (SLA)   |
| Incidentes  | Manual        | Processo formal    |
| Privacidade | Documentada   | Auditável          |
| Clientes    | SMB / Pro     | Enterprise         |

---

## 7. Relationship with ADRs

Este documento **precede e governa** todos os ADRs do Stage 3.

Todo ADR do Stage 3 deve:

* referenciar explicitamente este documento
* mapear qual capability enterprise está sendo atendida
* declarar impactos comerciais e operacionais

Nenhum ADR pode **contradizer** este STATUS.

---

## 8. Consequences

Ao definir explicitamente o Stage 3:

* reduzimos risco de promessas enterprise prematuras
* evitamos ADRs especulativos
* criamos uma base sólida para vendas enterprise
* preservamos coerência arquitetural no longo prazo

Este documento é **normativo**, não aspiracional.

---

## 9. Next Natural Step

Após este STATUS estar aprovado e versionado:

➡️ **ADR 0022 — Dedicated Runtime & Isolation Model**

Esse ADR será o **primeiro ADR legítimo do Stage 3**.

---

## 10. D1 — Dedicated Runtime Mode (Single-Tenant Enforcement)

**Objetivo (D1):**

* Habilitar um modo de runtime dedicado a um único tenant, com bloqueio explícito de requests para outros tenants.

**Flag de configuração:**

* `RUNTIME_DEDICATED_TENANT_ID=<tenant_id>` (quando setada, o runtime passa a operar em modo dedicado).

**Critérios de aceite:**

* Requests para `/api/v1/runtime/ask` com `tenant_id` diferente do tenant dedicado retornam **403** com erro estruturado.
* Requests com `tenant_id` igual ao tenant dedicado seguem o fluxo normal.
* Em modo default (flag ausente), não há mudança de comportamento.
* Testes específicos cobrem o modo dedicado.

**Como testar localmente:**

* `RUNTIME_DEDICATED_TENANT_ID=tenant-alpha CONTRACTOR_API_KEYS=dev-key pytest tests/integration/test_dedicated_runtime_mode.py`
* `curl -s -X POST http://localhost:8000/api/v1/runtime/ask -H 'X-API-Key: dev-key' -H 'Content-Type: application/json' -d '{"tenant_id":"tenant-alpha","question":"ping"}'`
* `curl -s -o /dev/null -w '%{http_code}\n' -X POST http://localhost:8000/api/v1/runtime/ask -H 'X-API-Key: dev-key' -H 'Content-Type: application/json' -d '{"tenant_id":"tenant-beta","question":"ping"}'`

---
