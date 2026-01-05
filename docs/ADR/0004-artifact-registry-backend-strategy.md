## ADR 0004 — Artifact Registry Backend Strategy (S3 + Metadata DB)

**(S3 + DB vs Git vs OCI Registry)**

**Status:** Accepted
**Data:** 2026-01-05
**Decisores:** SIRIOS / CONTRACTOR core team

### Contexto

O CONTRACTOR precisa armazenar e versionar **bundles imutáveis de artefatos** (ontologia, entidades, policies, templates, suites), com requisitos de:

* leitura frequente pelo runtime
* escrita controlada pelo control plane
* rollback rápido
* auditabilidade
* integração simples com AWS stage
* independência de fluxo de desenvolvimento (CI/CD ≠ produção)

O registry **não é um repositório de código**, mas um repositório de **artefatos operacionais versionados**.

### Decisão

Adotar **S3 como storage primário de bundles + banco relacional (metadata DB)** para controle de versões, aliases e auditoria.

* **S3**

  * armazena bundles imutáveis (diretórios compactados ou prefixos)
  * versionamento nativo habilitado
* **DB (Postgres/RDS)**

  * tenants
  * bundles (bundle_id, checksum, created_at)
  * aliases (`draft`, `candidate`, `current`)
  * trilha de auditoria (quem promoveu, quando, de onde)

Git **não** será backend primário de registry. OCI Registry **não** será usado no MVP.

### Alternativas consideradas

#### 1) Git como registry (repo por tenant ou mono-repo)

**Prós**

* versionamento humano amigável
* diffs claros
* workflow conhecido

**Contras**

* Git não é bom como backend de leitura de runtime
* acoplamento forte com CI/CD
* latência e complexidade para load dinâmico
* difícil garantir imutabilidade operacional
* não escala bem com muitos tenants

#### 2) OCI Registry (artefatos como imagens ou layers)

**Prós**

* imutabilidade forte
* bom para enterprise
* distribuição eficiente

**Contras**

* complexidade alta para MVP
* pouco amigável para bundles YAML/Jinja
* custo cognitivo alto para time e clientes
* ferramentas menos flexíveis para inspeção/debug

#### 3) **S3 + DB (decisão atual)**

**Prós**

* simples, robusto e barato
* integração nativa com AWS stage
* leitura rápida e paralela pelo runtime
* separação clara entre artefato e metadado
* fácil evoluir para OCI no futuro, se necessário

**Contras**

* diffs humanos menos naturais (mitigado por tooling)
* exige disciplina de checksum/manifest

### Implicações práticas

* Estrutura lógica no S3:

  ```
  s3://contractor-registry/
    tenants/{tenant_id}/
      bundles/{bundle_id}/
        manifest.yaml
        ontology/
        entities/
        policies/
        templates/
        suites/
  ```
* `manifest.yaml` é obrigatório e validado no upload.
* Control Plane é o **único** serviço autorizado a escrever no S3 registry.
* Runtime tem acesso **read-only** ao bucket (IAM role dedicada).
* Ferramentas de diff/export/import (scripts) serão fornecidas para:

  * comparação entre bundles
  * migração Araquem → CONTRACTOR
* Git continua sendo usado apenas como:

  * origem de desenvolvimento
  * backup/export
  * revisão humana (fora do runtime)

### Consequências (trade-off)

Escolha favorece **simplicidade operacional e previsibilidade** no MVP, sem bloquear evolução futura para OCI se algum cliente enterprise exigir.

---
