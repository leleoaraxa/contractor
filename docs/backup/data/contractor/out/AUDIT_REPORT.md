# CONTRACTOR — Audit Report (Docs vs Repo)
Data: 2026-01-05
Commit/branch: 94e8ae7 (work, clean tree)

## 1) Executive Summary
- Status geral: Stage 0 com avanços pontuais de Stage 1 (planner ativo), mas ausência de vários guardrails fundacionais.
- Top 5 conformidades fortes:
  1. Separação explícita entre Control Plane e Runtime com FastAPI dedicados e rotas distintas. (app/control_plane/api/main.py; app/runtime/api/main.py)
  2. Resolução de aliases draft/candidate/current por tenant armazenada em registry local, alinhada ao modelo de bundle imutável. (app/control_plane/domain/tenants/*; registry/control_plane/tenant_aliases.json)
  3. Validação estrutural mínima de bundles incluindo checagens de manifest e contratos de ontologia/policies. (app/control_plane/api/routers/bundles.py; app/control_plane/domain/bundles/contracts_validator.py)
  4. Runtime já consome manifest e planner_policy de bundle e produz decisão determinística com explain opcional. (app/runtime/api/routers/ask.py; app/runtime/engine/*)
  5. Camada de logging JSON com redaction básica aplicada a todos os registros. (app/shared/logging/logger.py; app/shared/logging/redact.py)
- Top 5 gaps críticos (impacto prático):
  1. Estrutura fundacional incompleta (ausência de várias pastas e componentes previstos: persistence, quality runner, observability, secrets, executor/builder/formatter). Impacta aderência ao FOUNDATION e ADRs 0005, 0008, 0011.
  2. Segurança baseline não implementada: sem auth/RBAC, sem secrets manager, sem sandbox de templates, sem policies de privacidade; risco direto a ADR 0007/0018. (app/*)
  3. Quality gates e promoção automatizada inexistentes; validação cobre apenas ontologia/policy básica e não executa suites nem gera relatórios. (app/control_plane/api/routers/bundles.py)
  4. Observabilidade limitada a logs; métricas/tracing tenant-aware ausentes, contrariando ADR 0006 e Foundation 2.6. (app/shared/logging/*)
  5. Runtime pipeline parcial: planner presente, porém builder/executor/cache/formatter/narrator inexistentes; impede cumprimento do pipeline Stage 0/1 e ADRs 0008/0011/0012.
- Recomendações priorizadas:
  1. Completar skeleton do runtime com builder/executor/formatter e cache tenant+bundle scoped para cumprir pipeline e ADR 0008/0011.  
  2. Implementar segurança mínima (auth/RBAC stubs, secrets interface, template sandbox) conforme ADR 0007/0011 e Foundation 2.5.  
  3. Ampliar Quality Gate: validar schema JSON, executar suites (data/quality) via control plane e gerar relatórios antes de promover aliases.  
  4. Introduzir observabilidade base (metrics/tracing tenant-aware) e rotulagem controlada conforme ADR 0006.  
  5. Fornecer .env.example, policies explicitas de versionamento/governança e completar docs C4/SECURITY para alinhar Foundation e Checklist Stage 0.

## 2) Repo Inventory (observável)
- Diretórios relevantes:
  - app/ (control_plane/, runtime/, shared/). (app/)
  - registry/ (tenants/demo/bundles/{202601050001,202601050002}, control_plane/tenant_aliases.json). (registry/)
  - data/quality/suites/*.json (routing/threshold suites). (data/quality/suites/)
  - contracts/ (JSON Schemas para ontologia/policies). (contracts/)
  - scripts/ (dev smoke/run_all, quality routing runner, release promote placeholder). (scripts/)
  - docs/ (FOUNDATION.md, ADRs 0001–0021, C4 placeholders). (docs/)
- Serviços e entrypoints:
  - Control Plane FastAPI app at app/control_plane/api/main.py; uvicorn via scripts/dev/run_control.ps1 e docker-compose service "control".
  - Runtime FastAPI app at app/runtime/api/main.py; uvicorn via scripts/dev/run_runtime.ps1 e docker-compose service "runtime".
  - Redis service declared but unused in code (docker-compose.yml).
- Endpoints identificados:
  - Control Plane: /api/v1/control/healthz; /tenants/{tenant_id}/aliases (GET/POST draft|candidate|current); /tenants/{tenant_id}/resolve/{release_alias}; /tenants/{tenant_id}/bundles/{bundle_id}/validate. (app/control_plane/api/routers/*.py)
  - Runtime: /api/v1/runtime/healthz; /ask (POST) com resolução de alias e planner. (app/runtime/api/routers/*.py)

## 3) Aderência ao docs/FOUNDATION.md
- 1) Árvore real de diretórios: ❌ Estrutura mínima não segue blueprint (faltam shared submódulos, persistence, quality, ops, tests, agents). (app/*; absence of many folders)
- 2.1 Missão/posicionamento: 🟡 README reflete missão e stage, mas sem enforcement formal ou artefatos adicionais. (README.md)
- 2.2 Princípios inegociáveis:
  - Control Plane ≠ Data Plane: ✅ Serviços separados com rotas próprias. (app/control_plane/api/main.py; app/runtime/api/main.py)
  - Tudo é contrato versionado: 🟡 Bundles usados para ontologia/policy, mas entidades/templates/suites inexistentes e policies parcial. (registry/tenants/demo/bundles/*)
  - Sem heurísticas/hardcode de domínio: 🟡 Planner determinístico sem domínio, porém mensagens e thresholds default codificados; falta policies mais amplas. (app/runtime/engine/planner/planner.py)
  - Isolamento por tenant: 🟡 Alias e manifest checam tenant_id, mas cache/conexões inexistentes; nenhum enforcement em métricas ou executor. (app/control_plane/domain/tenants/repository.py; app/runtime/engine/context/artifact_loader.py)
  - Compute-on-read: 🟡 Não há persistência, mas executor SQL inexistente; comportamento não testado. (app/runtime/engine)
  - Observabilidade/qualidade first-class: ❌ Apenas logging; sem métricas/traces/suites integradas. (app/shared/logging/*)
- 2.3 Modelo mental: 🟡 Bundles/aliases modelados, mas falta release alias default enforcement robusto e ausência de templates/policies completas. (app/runtime/api/routers/ask.py)
- 2.4 Contratos do Runtime: 🟡 Endpoint /ask aceita tenant/question e release_alias, mas não bloqueia parâmetros extras via payload; não há validação de campos proibidos. (app/runtime/api/routers/ask.py)
- 2.5 Segurança/compliance baseline: ❌ Sem auth, secrets, TLS handling, template sandbox ou políticas de redaction avançadas. (app/*)
- 2.6 Qualidade (Quality Gate v0): ❌ Validação estática parcial; sem suites dinâmicas ou relatórios. (app/control_plane/api/routers/bundles.py)
- 2.7 Versionamento/promoção/rollback: 🟡 Aliases file-backed e API para set/resolve, porém sem promoter, rollback automático ou atomicidade transacional. (app/control_plane/domain/tenants/*)
- 2.8 Política de mudanças/ADRs: 🟡 ADRs presentes, mas processo de migração/API-change não automatizado nem refletido em código. (docs/ADR/)
- 2.9 Multi-tenant isolamento prático: ❌ Sem cache/metrics scoping ou segregação de conexões; apenas validação de tenant_id/manifest. (app/shared/utils/ids.py; app/runtime/engine/context/*)
- 2.10 “Araquem como Tenant Zero”: ❌ Nenhum tenant Araquem ou suite dedicada; apenas demo tenant. (registry/tenants/demo)

## 4) Aderência ao docs/CHECKLIST-STAGE-0.md
- Repositório & Estrutura:
  - Repositório criado: DONE (git tree).
  - Estrutura de pastas conforme arquitetura: MISSING (diversos diretórios ausentes). (app/*)
  - README fundacional: DONE. (README.md)
  - docs/FOUNDATION.md com Guardrails v0: DONE. (docs/FOUNDATION.md)
  - docs/ADR/ 0001–0021: DONE. (docs/ADR/)
  - Licença definida: MISSING (no LICENSE file). (repo root)
  - .env.example criado: MISSING. (repo root)
- Guardrails & Governança:
  - ADRs versionados/imutáveis: DONE (present, accepted). (docs/ADR/)
  - Processo ADR documentado: PARTIAL (ADRs exist, no contributing/process doc). (docs/ADR/)
  - Política “no hardcode / no heuristics”: PARTIAL (stated in README, not enforced). (README.md; code)
  - Política de versionamento de bundles definida: DONE (manifests + aliases). (registry/*; app/control_plane/domain/tenants/*)
  - Papéis/responsabilidades documentados: MISSING (no RBAC/auth docs). (docs/)
- Control Plane — Skeleton:
  - API healthz: DONE. (app/control_plane/api/routers/healthz.py)
  - Modelo Tenant definido: PARTIAL (aliases only, no tenant metadata). (app/control_plane/domain/tenants/models.py)
  - Modelo Artifact/Bundle definido: PARTIAL (manifest + validator, sem registry backend/metadata DB). (app/control_plane/api/routers/bundles.py)
  - Registry local funcional: DONE (filesystem loader). (app/runtime/engine/context/artifact_loader.py)
  - Alias model draft/candidate/current implementado: DONE (alias store + endpoints). (app/control_plane/domain/tenants/*)
  - Audit log básico: MISSING.
- Runtime — Skeleton:
  - API healthz: DONE. (app/runtime/api/routers/healthz.py)
  - TenantContext implementado: DONE (minimal). (app/runtime/engine/context/tenant_context.py)
  - ArtifactLoader funcional: DONE (filesystem). (app/runtime/engine/context/artifact_loader.py)
  - Pipeline planner/builder/executor/formatter stubs encadeados: PARTIAL (planner active; others absent). (app/runtime/engine/*)
  - Nenhuma lógica de domínio: DONE (demo artifacts only; code domain-agnostic). (app/runtime/engine/planner/planner.py)
- Bundle Model (Formato):
  - Estrutura definida/documentada: PARTIAL (manifest + ontology/policy; no entities/templates/suites in code). (registry/tenants/demo/bundles/*)
  - manifest.yaml obrigatório/validado: DONE. (app/control_plane/api/routers/bundles.py)
  - Exemplo bundle mínimo funcional: DONE (demo bundles). (registry/tenants/demo/bundles/*)
  - Inclui ontology/entities/policies/templates/suites: PARTIAL (ontology/policies present; entities minimal; templates/suites missing in bundle layout). (registry/tenants/demo/bundles/*)
- Quality & Validation:
  - Validação estática: PARTIAL (ontology/policy checks only). (app/control_plane/domain/bundles/contracts_validator.py)
  - Smoke test /ask com bundle mínimo: PARTIAL (smoke.ps1 hits /ask but not automated tests). (scripts/dev/smoke.ps1)
  - Relatório de validação gerado: MISSING.
  - Nenhuma promoção sem validação: MISSING (aliases can be set without validation gate).
- Segurança Base:
  - Redaction layer obrigatória: PARTIAL (logging redact only; no request/response redaction). (app/shared/logging/redact.py)
  - Nenhum segredo em código/config: DONE (no secrets found; env-driven). (settings)
  - Templates sandboxed: MISSING (no template engine implemented). (app/runtime)
  - Logs sem dados sensíveis: PARTIAL (redaction basic; no PII controls). (app/shared/logging/redact.py)
- Observabilidade Base:
  - Métricas requests/errors/latency: MISSING.
  - Labels tenant-aware: MISSING.
  - Logs estruturados: DONE (JSON logger). (app/shared/logging/logger.py)
  - Sem cardinalidade explosiva: UNKNOWN (no metrics implemented).
- Tenant Zero (Araquem):
  - Tenant zero definido/bundle/smoke: MISSING (only demo tenant).
- Critério de Saída Stage 0:
  - Plataforma sobe localmente: PARTIAL (scripts for uvicorn; not validated).
  - Bundle mínimo carregado: DONE (demo manifest consumed).
  - /ask determinístico responde: DONE (planner deterministic). (app/runtime/api/routers/ask.py)
  - Nenhum hardcode de domínio: PARTIAL (demo wording but no domain logic).
  - ADRs governam decisões: PARTIAL (ADRs exist; implementation incomplete).
  - Explicação sem ambiguidade: PARTIAL (docs present, but missing components).

## 5) Aderência aos ADRs (docs/ADR/0001–0021)
- ADR 0001 — Separação Control Plane vs Data Plane  
  - Decisão: serviços separados; runtime só executa bundles promovidos; control plane governa aliases.  
  - Evidências: app/control_plane/api/main.py; app/runtime/api/main.py; app/runtime/api/routers/ask.py; app/control_plane/api/routers/tenants.py.  
  - Estado: IMPLEMENTADO (básico).  
  - Divergências: falta auth e isolamento de rede; control plane não persiste metadados.  
  - Next steps: adicionar auth/authorization; persistência real para aliases; enforce runtime read-only scope.
- ADR 0002 — Modelo de versionamento e empacotamento  
  - Decisão: bundle imutável + aliases draft/candidate/current; manifest obrigatório.  
  - Evidências: registry/tenants/demo/bundles/*/manifest.yaml; app/control_plane/api/routers/bundles.py; app/control_plane/domain/tenants/repository.py.  
  - Estado: IMPLEMENTADO (mínimo).  
  - Divergências: falta promoter/rollback automático; manifest não valida checksum; bundles carecem templates/suites.  
  - Next steps: implementar promoter com checksum; enforcement de validação antes de setar aliases; completar artefatos.
- ADR 0003 — Isolamento multi-tenant  
  - Decisão: pool compartilhado com opção dedicada; cache/metrics/conexões devem ser tenant-scoped.  
  - Evidências: tenant_id validation and alias store (app/shared/utils/ids.py; app/control_plane/domain/tenants/repository.py).  
  - Estado: PARTIAL.  
  - Divergências: nenhum cache/executor/metrics isolado; sem hash/alias em observabilidade.  
  - Next steps: introduzir cache e executores com chave tenant+bundle; métricas com tenant_ref; testes de isolamento.
- ADR 0004 — Artifact registry backend (S3 + DB)  
  - Decisão: usar S3 + metadata DB; control plane único escritor.  
  - Evidências: filesystem loader/validator (app/runtime/engine/context/artifact_loader.py; app/control_plane/api/routers/bundles.py).  
  - Estado: NOT IMPLEMENTED (fora S3/DB; apenas FS local).  
  - Divergências: sem DB, sem metadata, sem controle de escrita/leitura; runtime e control compartilham pasta montada.  
  - Next steps: abstrair registry backend; adicionar metadata store; IAM-like separation.
- ADR 0005 — Client data connectivity (direct vs agent)  
  - Decisão: conexão direta MVP; agente opcional futuro; executor abstraído.  
  - Evidências: ausência de executor abstrações; docker-compose inclui Redis apenas.  
  - Estado: NOT IMPLEMENTED.  
  - Divergências: nenhum executor DB, nenhuma interface base ou agent stub.  
  - Next steps: criar executor base + PostgresDirect stub; definir interface para agent.
- ADR 0006 — Observabilidade multi-tenant  
  - Decisão: métricas tenant-aware controladas; redaction; tracing com tenant_ref.  
  - Evidências: apenas logging JSON + redaction básica. (app/shared/logging/*)  
  - Estado: NOT IMPLEMENTED (metrics/tracing).  
  - Divergências: sem métricas/traces; logs não incluem tenant_ref; risco de baixa visibilidade.  
  - Next steps: adicionar metrics module com tenant_ref; tracing hooks; ensure redact coverage.
- ADR 0007 — Security baseline & threat model  
  - Decisão: auth obrigatório, secrets manager, TLS, sandbox templates, audit log.  
  - Evidências: none (no auth/secrets/audit).  
  - Estado: NOT IMPLEMENTED.  
  - Divergências: runtime/control abertos; sem secret handling; sem audit log.  
  - Next steps: add authn/z stubs, secrets interface, audit trail for alias changes.
- ADR 0008 — Runtime caching strategy  
  - Decisão: cache tenant+bundle scoped; TTL policy-driven.  
  - Evidências: no cache code.  
  - Estado: NOT IMPLEMENTED.  
  - Divergências: no cache layers; thresholds not cached; risk of latency.  
  - Next steps: design rt_cache service keyed by tenant+bundle; metrics for hits/misses.
- ADR 0009 — Quality gates and promotion criteria  
  - Decisão: static+dynamic validation, routing suites, security checks; promotion with report.  
  - Evidências: static validator for ontology/policy; routing suites JSON not integrated. (app/control_plane/domain/bundles/contracts_validator.py; data/quality/suites/*)  
  - Estado: PARTIAL.  
  - Divergências: no dynamic execution, no reports, aliases can be set without gates.  
  - Next steps: integrate run_routing_suite into control plane; store quality reports; block promotion on failure.
- ADR 0010 — Planner and ontology resolution  
  - Decisão: ontology-driven deterministic planner with thresholds/policy; explain structured.  
  - Evidências: OntologyLoader + Planner using policy/planner.yaml; ask endpoint uses explain flag. (app/runtime/engine/ontology/ontology_loader.py; app/runtime/engine/planner/planner.py; app/runtime/api/routers/ask.py)  
  - Estado: IMPLEMENTADO (v1).  
  - Divergências: no LLM optional path, no scoring weights from ontology; limited ontology fields.  
  - Next steps: expand ontology schema (weights/synonyms); add explain route; policy-driven thresholds validation.
- ADR 0011 — Template rendering and output safety  
  - Decisão: Jinja sandbox allowlist; validation static/dynamic.  
  - Evidências: templates directory absent; no renderer.  
  - Estado: NOT IMPLEMENTED.  
  - Divergências: runtime returns static string; no sandbox.  
  - Next steps: implement sandboxed renderer with allowlist; control-plane validator for templates.
- ADR 0012 — RAG integration and knowledge boundaries  
  - Decisão: RAG opt-in, additive only, no numeric authority.  
  - Evidências: no RAG components.  
  - Estado: NOT IMPLEMENTED.  
  - Divergências: none implemented.  
  - Next steps: add policy parsing for RAG enabled/disabled; guardrails in runtime pipeline.
- ADR 0013 — Rate limiting, quotas, cost controls  
  - Decisão: policy-driven limits per tenant endpoint; Redis-backed token bucket.  
  - Evidências: no rate limit code; Redis unused.  
  - Estado: NOT IMPLEMENTED.  
  - Divergências: runtime accepts unlimited requests; no quotas/billing metrics.  
  - Next steps: add middleware for rate limiting; capture consumption metrics; expose errors on limit exceed.
- ADR 0014 — API contracts and backward compatibility  
  - Decisão: versioned paths (/api/v1/*), backward compatibility; deprecation policy.  
  - Evidências: APIs under /api/v1/control and /api/v1/runtime. (app/control_plane/api/main.py; app/runtime/api/main.py)  
  - Estado: IMPLEMENTADO (path versioning only).  
  - Divergências: no OpenAPI contracts or schema validation; no deprecation process.  
  - Next steps: publish OpenAPI docs; add contract tests; document deprecation.
- ADR 0015 — Deployment environments & release lifecycle  
  - Decisão: local/dev/stage/prod; promote artifacts not rebuild; rollback first-class.  
  - Evidências: settings.environment default local; docker-compose local; alias-based rollback manual. (app/shared/config/settings.py; docker-compose.yml)  
  - Estado: PARTIAL.  
  - Divergências: no environment-specific configs or pipelines; rollback not automated.  
  - Next steps: add env configs, runbooks; automate rollback via alias switch API with audit.
- ADR 0016 — SDKs and client integration strategy  
  - Decisão: API-first; thin SDKs Python/JS.  
  - Evidências: none (no SDKs).  
  - Estado: NOT IMPLEMENTED.  
  - Divergências: n/a.  
  - Next steps: publish OpenAPI + starter SDK stubs aligned to /api/v1.
- ADR 0017 — Billing, metering, commercial plans  
  - Decisão: metering dimensions per tenant; quotas; plans Starter/Pro/Enterprise.  
  - Evidências: no metering or plans.  
  - Estado: NOT IMPLEMENTED.  
  - Divergências: no metrics, no plan enforcement.  
  - Next steps: add metering capture (requests, SQL time); plan config in control plane; quota enforcement.
- ADR 0018 — Data privacy, LGPD/GDPR & retention  
  - Decisão: privacy-by-design, retention policies, data classes A–D.  
  - Evidências: minimal redaction only; no retention policies.  
  - Estado: NOT IMPLEMENTED.  
  - Divergências: no classification, no retention controls, no data handling docs.  
  - Next steps: add retention config per class; expand redaction; doc processor/controller roles.
- ADR 0019 — Incident management and SLOs  
  - Decisão: SEV levels, SLOs, postmortems.  
  - Evidências: none (no SLO metrics/runbooks).  
  - Estado: NOT IMPLEMENTED.  
  - Divergências: no alerts or postmortem process.  
  - Next steps: define SLO metrics and dashboards; add incident runbooks in docs/RUNBOOKS.
- ADR 0020 — Governance model and change management  
  - Decisão: ADR-driven governance; change classification; communication.  
  - Evidências: ADRs exist; no change process or changelog.  
  - Estado: PARTIAL.  
  - Divergências: no documented flow for reviewing/approving changes; no audit log.  
  - Next steps: add governance doc; enforce ADR requirement in PR template; start changelog.
- ADR 0021 — Product roadmap and maturity stages  
  - Decisão: stage-based maturity (0–4) with criteria; no skipping stages.  
  - Evidências: README declares Stage 0; no stage gating in code. (README.md)  
  - Estado: PARTIAL.  
  - Divergências: pipeline includes Stage1 planner without clarity; no tracking of stage exit criteria.  
  - Next steps: map backlog to stages; enforce stage criteria checks in release process.

## 6) Stage Map (realidade vs planejado)
- Pronto no Stage 0:
  - Control Plane/Runtime services boot with healthz.
  - Alias resolution and manifest validation for bundles.
  - Demo bundle registry with ontology/policy and deterministic planner execution on /ask.
  - JSON logging with basic redaction.
- Entrou em Stage 1:
  - Planner v1 com thresholds via policy/planner.yaml e explain opcional em runtime. (app/runtime/engine/planner/planner.py; registry/tenants/demo/bundles/*/policies/planner.yaml)
- Ainda inexistente:
  - Builder/executor/cache/formatter/narrator pipelines; RAG integration; policy enforcement beyond planner.
  - Secrets management, auth/RBAC, audit log, rate limiting/quotas, metering/billing.
  - Observability metrics/tracing; quality runner integrated; promotion gating; rollback automation.
  - Templates sandboxed; agent connectivity; ops/runbooks; tests suite.

## 7) Quality & DX
- Scripts:
  - scripts/dev/run_control.ps1 & run_runtime.ps1 start uvicorn for services; run_all.ps1 runs both. (scripts/dev/*.ps1)
  - scripts/dev/smoke.ps1 performs healthz, bundle validate, alias set, and /ask smoke (requires running services). (scripts/dev/smoke.ps1)
  - scripts/quality/run_routing_suite.py posts cases from data/quality/suites to runtime /ask to check routing decisions. (scripts/quality/run_routing_suite.py)
  - scripts/release/promote_candidate_to_current.ps1 placeholder (empty content). (scripts/release/promote_candidate_to_current.ps1)
- Suites/coverage:
  - data/quality/suites/*.json define routing/threshold cases for tenant demo; no integration with control plane or CI. (data/quality/suites/)
  - No unit/integration tests present.
- Error handling/observations:
  - Control plane validate_bundle aggregates contract errors but no audit; runtime ask falls back to stable schema on planner errors. (app/control_plane/api/routers/bundles.py; app/runtime/api/routers/ask.py)
  - Redaction applies to logs only; no PII detection in payloads.

## 8) Findings (Prioritized)
- P0: Security baseline absent (auth/secrets/audit/log retention), exposing all endpoints unauthenticated and risking tenant leakage. Evidence: app/control_plane/api/main.py; app/runtime/api/main.py; app/shared/config/settings.py. Impact: high security risk and non-compliance with ADR 0007/0018. Mitigation: introduce authn/z stubs, secrets interface, audit logging, and TLS/network notes.
- P0: Runtime pipeline incomplete (no builder/executor/cache/formatter), blocking true /ask execution and compute-on-read promise. Evidence: app/runtime/engine/* (planner only). Impact: platform cannot execute data queries; Stage 0 exit criteria unmet. Mitigation: add stub modules and wire into /ask with tenant/bundle scoping and cache keys.
- P1: Quality gates/promotion flow missing; aliases can be set without validation or reports. Evidence: app/control_plane/api/routers/tenants.py; app/control_plane/api/routers/bundles.py. Impact: risk of promoting broken bundles; no audit trail. Mitigation: enforce validation+quality runner before alias changes; store reports.
- P1: Observability tenant-awareness missing (metrics/tracing absent). Evidence: app/shared/logging/* only. Impact: inability to monitor SLOs or detect noisy tenants; ADR 0006 non-compliant. Mitigation: add metrics module with tenant_ref/bundle_id labels; tracing hooks; dashboards.
- P2: Documentation/ops gaps (.env.example, LICENSE, runbooks, C4 diagrams empty). Evidence: repo root; docs/C4/*.md empty. Impact: onboarding friction and governance ambiguity. Mitigation: add env sample, license, runbooks, and fill C4 diagrams per FOUNDATION.

