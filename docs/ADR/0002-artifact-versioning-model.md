## ADR 0002 — Modelo de versionamento e empacotamento de artefatos (Bundle Imutável + Aliases)

**Status:** Accepted
**Data:** 2026-01-05
**Decisores:** SIRIOS / CONTRACTOR core team

**Contexto**
O produto deve permitir que cada tenant edite e publique contratos sem quebrar produção, e com rollback rápido. Precisamos de:

* rastreabilidade (qual conjunto de artefatos gerou qual resposta)
* consistência (ontologia/entidades/templates/policies compatíveis)
* promoção controlada (draft → candidate → current)

**Decisão**
Adotar modelo de **Bundle imutável** + **aliases de release** por tenant:

* **Bundle**: diretório/artefato imutável com `bundle_id` (ex.: `YYYYMMDDHHMMSSxxxx`) contendo:

  * `manifest.yaml`
  * `ontology/*`
  * `entities/*`
  * `policies/*`
  * `templates/*`
  * `suites/*` (opcional)
* **Aliases** por tenant: `draft`, `candidate`, `current`

  * `draft`: editável
  * `candidate`: imutável, produzido via “build/promote” do draft validado
  * `current`: ponteiro atômico para um `candidate` aprovado

O runtime executa sempre com `bundle_id` resolvido, e todos os logs/métricas devem registrar `tenant_id` e `bundle_id`.

**Alternativas consideradas**

1. **Artefatos soltos versionados individualmente** (cada arquivo tem versão própria)
2. **Git como fonte única (branch/tag) por tenant**
3. **Bundle imutável + aliases** (decisão atual)

**Prós (decisão atual)**

* Consistência forte: o runtime sempre enxerga um conjunto coerente.
* Rollback trivial: trocar `current` para bundle anterior.
* Auditabilidade: cada resposta referencia explicitamente `bundle_id`.
* Facilita caching: chave de cache inclui `tenant_id + bundle_id`.

**Contras**

* Pode haver duplicação de arquivos entre bundles (custo de storage).
* Promoção exige um “build step” (gerar candidate a partir do draft).

**Implicações práticas**

* Control plane implementa:

  * `ArtifactValidator`: valida YAML/schema e compatibilidade cruzada
  * `Promoter`: gera `candidate` imutável
  * `AliasManager`: aponta `current → candidate_id` de forma atômica
* Runtime implementa:

  * `ArtifactLoader`: carrega bundle por `tenant_id + alias` e resolve para `bundle_id`
  * registro obrigatório de `bundle_id` em `meta`
* `manifest.yaml` deve conter, no mínimo:

  * `bundle_id`, `tenant_id`, `created_at`, `source` (ex.: “draft”), `checksum`
  * lista de artefatos presentes (paths) e versões internas se aplicável
* Testes:

  * suite de “bundle integrity” (tudo que a ontologia referencia existe; templates referenciam campos válidos, etc.)

**Consequências (trade-off)**
Storage cresce, porém estabilidade e governança aumentam. Esse trade-off é favorável para B2B.

---
