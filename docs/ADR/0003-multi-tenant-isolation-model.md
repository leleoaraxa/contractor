## ADR 0003 — Modelo de isolamento multi-tenant: Runtime Pool compartilhado (default) + opção de Runtime dedicado (Enterprise)

**Status:** Accepted
**Data:** 2026-01-05
**Decisores:** SIRIOS / CONTRACTOR core team

**Contexto**
O produto precisa suportar muitos tenants com custo controlado, mantendo isolamento de dados, cache e execução. Há duas estratégias:

* runtime compartilhado (pool)
* runtime dedicado por tenant

**Decisão**
Adotar **Runtime Pool multi-tenant compartilhado como default**, com capacidade de evoluir para **Runtime dedicado por tenant** no plano enterprise.

Na prática:

* Default: um conjunto de instâncias do runtime atende múltiplos tenants (request-scoped `tenant_id`).
* Enterprise: provisiona instâncias (ou namespace) dedicadas para tenants com requisitos rígidos de compliance/performance.

**Alternativas consideradas**

1. **Runtime dedicado por tenant para todos**
2. **Runtime compartilhado para todos, sem opção dedicada**
3. **Híbrido: pool default + dedicado enterprise** (decisão atual)

**Prós (decisão atual)**

* Economia e escala: pool compartilha capacidade e reduz custo médio.
* Velocidade de evolução: upgrades e patches centralizados.
* Flexibilidade comercial: oferecer isolamento forte como upsell enterprise.

**Contras**

* Isolamento deve ser rigorosamente implementado (risco de “leakage” lógico).
* Observabilidade pode ter cardinalidade alta (labels por tenant).
* Debugging multi-tenant é mais complexo.

**Implicações práticas**

* Regras de isolamento obrigatórias:

  * Cache keys incluem `tenant_id + bundle_id`
  * Qualquer armazenamento temporário (Redis, fila, memória) é particionado por tenant
  * Conexões de DB são tenant-scoped (pool por tenant ou pool compartilhado com DSN/credenciais por tenant)
  * Logs e métricas devem evitar dados sensíveis; aplicar `redact` central
* Quotas e rate limits precisam ser aplicados por tenant (Control plane define; runtime aplica).
* Observabilidade:

  * `tenant_id` deve ser representado como **alias/hash estável** para reduzir cardinalidade, quando necessário.
* Testes P0:

  * suíte de “cross-tenant isolation” (garantir que tenant A não acessa cache/artefatos/conn de tenant B)
  * testes de concorrência (requests simultâneos com tenants diferentes)

**Consequências (trade-off)**
O modelo híbrido permite começar com custo baixo e manter caminho para compliance alto. A exigência é disciplina forte de isolamento e suites de validação dedicadas.

---
