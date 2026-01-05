## ADR 0001 — Separação Control Plane vs Data Plane

**Status:** Accepted
**Data:** 2026-01-05
**Decisores:** SIRIOS / CONTRACTOR core team
**Contexto**
CONTRACTOR precisa suportar multi-tenant, versionamento de artefatos (ontologia, entidades, policies, templates, suites) e execução (/ask) com governança e auditabilidade. Misturar “editar/promover” com “executar” tende a gerar acoplamento, risco de segurança e degradação de confiabilidade.

**Decisão**
Adotar separação rígida entre:

* **Control Plane**: governa tenants, conexões, artefatos, validação, promoção de versões e execução de suites de qualidade.
* **Data Plane (Runtime)**: executa requests (/ask) apenas contra releases promovidos (default `current`) e não possui capacidades de edição/promoção.

A separação se refletirá em código e deploy:

* `app/control_plane/*`
* `app/runtime/*`

**Alternativas consideradas**

1. **Monólito único** (uma API para tudo)
2. **Control Plane + Runtime separados** (decisão atual)

**Prós (decisão atual)**

* Isolamento de risco: erros do runtime não corrompem governança; problemas de edição não derrubam /ask.
* Segurança: superfície de ataque do runtime reduzida; menor risco de expor endpoints administrativos.
* Operação: escalonamento independente (runtime scale-out; control plane mais estável).
* Multi-tenant: mais fácil garantir segregação quando o runtime é “stateless executor”.

**Contras**

* Mais serviços e disciplina operacional (deploy, observabilidade e CI/CD em dois componentes).
* Necessidade de contratos internos (p.ex. como o runtime resolve `tenant_id + alias`).

**Implicações práticas**

* O runtime **não** terá endpoints de upload/edição/promote.
* O control plane será a fonte de verdade de “qual bundle está em `current`”.
* O runtime deverá implementar `TenantContext` e `ArtifactLoader` capazes de resolver:

  * `tenant_id`
  * `release_alias` (draft/candidate/current; por padrão `current`)
  * `bundle_id` final resolvido
* Testes de isolamento e regressão devem ser divididos:

  * control plane: validação de artefatos, RBAC, promoção e auditoria
  * runtime: execução, cache segregado, performance, redaction

**Consequências (trade-off)**
A complexidade de infra cresce, mas a previsibilidade e segurança do produto aumentam significativamente; isso viabiliza o roadmap enterprise (isolamento, auditoria e compliance).

---
