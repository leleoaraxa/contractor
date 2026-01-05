## 1) Árvore real de diretórios (CONTRACTOR)

Objetivo da árvore: separar, de forma inequívoca, **Control Plane**, **Runtime (Data Plane)** e **Artefatos versionados**. Mantém também “ops” e “quality” como primeira classe (coerente com o DNA do Araquem).

```
contractor/
  README.md
  LICENSE
  pyproject.toml
  uv.lock (ou poetry.lock)
  .env.example
  .gitignore

  docs/
    FOUNDATION.md                     # Guardrails v0 + visão do produto (imutável por seção)
    ADR/
      0001-control-plane-vs-data-plane.md
      0002-artifact-versioning-model.md
      0003-multi-tenant-isolation-model.md
    C4/
      context.md
      container.md
      component.md
    RUNBOOKS/
      local-dev.md
      deploy-aws.md
      incident-response.md
    SECURITY/
      threat-model.md
      data-handling.md

  app/
    __init__.py

    shared/                           # código cross-plane (baixo acoplamento)
      config/
        settings.py                   # leitura env + defaults estritos
      logging/
        logger.py
        redact.py                     # redaction (PII/segredos) - padrão
      observability/
        metrics.py
        tracing.py
      errors/
        exceptions.py
      utils/
        time.py
        hashing.py
        ids.py

    control_plane/
      api/
        main.py                       # FastAPI (ou gateway) do Control Plane
        routers/
          healthz.py
          tenants.py                  # CRUD tenants + RBAC hooks
          connections.py              # datasources (sem segredos no payload)
          artifacts.py                # upload/validate/promote
          versions.py                 # draft/candidate/current
          quality.py                  # run suites + reports
        deps/
          auth.py                     # authn/authz
          rate_limit.py
        contracts/
          openapi_notes.md

      domain/
        tenants/
          models.py
          service.py
          repository.py
        connections/
          models.py
          service.py
          repository.py
          secrets.py                  # integração KMS/Secrets Manager (interface)
        artifacts/
          models.py                   # Artifact, Bundle, Manifest
          registry.py                 # S3/Git-backed (interface)
          validator.py                # validação estática (YAML/JSONSchema)
          promoter.py                 # draft->candidate->current
        quality/
          runner.py                   # executa suites contra runtime
          reports.py                  # normaliza output
        audit/
          log.py                      # trilha de auditoria

      persistence/
        db.py                         # metadata DB (tenants, versions, audit)
        migrations/                   # alembic, etc.

    runtime/
      api/
        main.py                       # /ask runtime (Data Plane)
        routers/
          ask.py                      # endpoint de execução
          healthz.py
          metrics.py
      engine/
        context/
          tenant_context.py           # carrega tenant_id + version + policies
          artifact_loader.py          # resolve current/candidate
        planner/
          router.py                   # roteamento genérico via ontologia
          scoring.py
        builder/
          sql_builder.py              # gera SQL parametrizado via contratos
        executor/
          db/                         # conectores
            base.py
            postgres.py               # MVP
          cache/
            rt_cache.py               # cache segregado por tenant
        formatter/
          rows.py
          templating.py               # Jinja + sandbox
        narrator/
          narrator.py                 # opcional, policy-driven
          prompts.py
        quality_hooks/
          gate.py                     # hooks por request (não bloqueantes no MVP)
      policies/
        enforcement.py                # aplica policies do bundle

    agents/
      db_agent/                       # opcional (fase futura)
        README.md
        client.py
        server.py
        mTLS/
          certs.md

  registry/                           # artefatos versionados (exemplo local)
    tenants/
      demo/
        bundles/
          202601050001/
            manifest.yaml
            ontology/
              entity.yaml
              intents.yaml
            entities/
              catalog.yaml
              fiis_cadastro.yaml    # exemplo apenas (não “hardcode”, é conteúdo do bundle)
            policies/
              cache.yaml
              quality.yaml
              rag.yaml
              narrator.yaml
            templates/
              fiis_cadastro/table.md.j2
            suites/
              routing_suite.json
              entities_sql_suite.json

  ops/
    compose/
      compose.dev.yaml
      compose.stage.yaml
    grafana/
      dashboards/
      provisioning/
    prometheus/
      prometheus.yaml
    tempo/
      tempo.yaml
    otel/
      collector.yaml

  scripts/
    dev/
      seed_demo_tenant.py             # carrega demo tenant local
      lint_artifacts.py               # valida bundles offline
    quality/
      run_suite.py                    # runner CLI
      diff_answers.py                 # diff estruturado de respostas
    tools/
      export_bundle.py                # export Araquem -> Contractor bundle
      import_bundle.py

  tests/
    unit/
      control_plane/
      runtime/
      shared/
    integration/
      api_contracts/
      multi_tenant_isolation/
      postgres_connector/
    fixtures/
      bundles/
        minimal_bundle/

  .github/
    workflows/
      ci.yaml
      security.yaml

```

### Observações operacionais

* **`registry/`** existe como “formato de bundle” (artefato) e também como **exemplo local** para dev. Em produção, o registry real deve ser **S3 + metadados no DB** (ou Git/OCI, decisão por ADR).
* **`app/shared/`** precisa ser minimalista; se crescer demais vira acoplamento ruim.
* Tudo que for “conteúdo de domínio” vive em **bundles** (ex.: `registry/tenants/.../bundles/...`), nunca em código.

---

## 2) Guardrails v0 — CONTRACTOR (fundacional)

A seguir está o texto do **FOUNDATION.md** (Guardrails v0). Você pode colar em `docs/FOUNDATION.md`.

### 2.1. Missão e posicionamento

**CONTRACTOR** é uma plataforma multi-tenant para execução de experiências analíticas e respostas (/ask) baseada em **contratos versionados** (ontologia, entidades, políticas e templates). O sistema prioriza **determinismo, auditabilidade e governança**.

**CONTRACTOR não é um produto de um domínio específico.** Qualquer domínio (FIIs, varejo, SaaS, indústria) é “plugado” via bundles de artefatos.

### 2.2. Princípios inegociáveis

1. **Control Plane ≠ Data Plane**

   * Control Plane governa, valida e promove versões.
   * Data Plane executa somente versões promovidas, sem editar nada.

2. **Tudo é contrato versionado**

   * Ontologia, catálogo de entidades, schemas, policies, templates, suites.
   * Não existe “config manual no runtime”.

3. **Sem heurísticas e sem hardcode de domínio**

   * Qualquer lógica de roteamento, seleção de entidades, agregações e limites deve ser orientada pelos contratos/policies do bundle.
   * Exceções de cliente/domínio são modeladas como **artefatos** (não como if/else em código).

4. **Isolamento por tenant é requisito funcional**

   * Segredos, cache, métricas, rate limits e artefatos devem ser segregados.
   * “Cross-tenant leakage” é bug P0.

5. **Compute-on-read por padrão**

   * CONTRACTOR executa queries reais em fontes do cliente.
   * Persistência de dados do cliente é proibida (exceto cache efêmero e logs redigidos).

6. **Observabilidade e qualidade são first-class**

   * Sem métricas e suites mínimas, feature não entra.
   * A plataforma deve oferecer “evidência” do comportamento.

### 2.3. Modelo mental do produto

* **Tenant**: unidade de isolamento e faturamento.
* **Artifact**: componente versionável (ontologia, entidade, policy, template).
* **Bundle**: conjunto imutável de artifacts com `bundle_id` (ex.: `YYYYMMDDHHMMSSxxxx`).
* **Release alias**: `draft`, `candidate`, `current`.
* **Runtime execution** sempre referencia `tenant_id + release_alias`.

### 2.4. Contratos do Runtime

O Data Plane aceita um payload mínimo (exemplo conceitual):

* `tenant_id`
* `question`
* `conversation_id` (opcional)
* `client_id` (opcional)
* `release_alias` (opcional; default `current`)

**Proibição:** o runtime não aceita “parâmetros de janela, agregação, limit, order” via querystring/payload para manipular SQL.
Essas escolhas são inferidas e validadas via contratos/policies.

### 2.5. Segurança e compliance (baseline)

1. **Segredos**

* Nunca trafegar segredo em logs.
* Segredos armazenados em Secrets Manager/KMS (ou equivalente), acessados via interface `secrets.py`.

2. **PII/Privacidade**

* Redaction obrigatória em logs e shadow.
* Proibição de logar linhas brutas de entidades “privadas” (policy-driven).

3. **Conectividade**

* MVP: TLS + allowlist.
* Enterprise: agent + mTLS + private networking.

4. **Templates**

* Renderização em sandbox (limitar filtros e funções expostas).
* Proibição de execução arbitrária no template.

### 2.6. Qualidade (Quality Gate v0)

Para cada bundle `candidate`, o Control Plane deve produzir:

* validação estática:

  * YAML parse
  * schema validation (JSONSchema/contratos)
  * consistência ontologia ↔ catálogo de entidades ↔ templates
* validação dinâmica:

  * suite mínima de roteamento (top1 / gap / routed-rate)
  * suite de entidades SQL-only (pelo menos 1 por entidade crítica)
  * smoke test de /ask

Critérios mínimos recomendados (ajustáveis por tenant/policy):

* `routed_rate >= 0.98`
* `top1_accuracy >= 0.93` (MVP) e objetivo `>= 0.95`
* `gap_p50 >= 0.0` (ou policy-driven)
* `0` vazamentos cross-tenant em testes

### 2.7. Versionamento, promoção e rollback

* `draft`: editável; pode falhar.
* `candidate`: imutável; gerado a partir de draft validado; tem relatório de qualidade.
* `current`: alias apontando para um candidate aprovado.
* rollback: trocar `current` para candidate anterior (operação atômica).

### 2.8. Política de mudanças (para evitar retrabalho)

* Toda decisão arquitetural relevante vira **ADR numerada**.
* ADR deve conter:

  * contexto
  * decisão
  * alternativas consideradas
  * consequências (trade-offs)
* Mudanças de contrato de API exigem:

  * doc de impacto
  * plano de migração
  * suite atualizada

### 2.9. Multi-tenant: isolamento obrigatório (regras práticas)

* Cache key SEMPRE inclui `tenant_id + bundle_id`.
* Métricas SEMPRE incluem label `tenant_id` (com cuidado para cardinalidade; usar hash/alias se necessário).
* O loader de artifacts não pode usar estado global compartilhado sem particionamento.
* Toda conexão de datasource deve ser “scoped” ao tenant.

### 2.10. “Araquem como Tenant Zero”

* Araquem é tratado como tenant referência (gold standard).
* Todo release do CONTRACTOR deve rodar suite do tenant Araquem:

  * se quebrar, bloqueia merge.
* Migração de contratos Araquem → Contractor deve ser feita por script (`export_bundle.py`), sem copiar “na mão”.

---
