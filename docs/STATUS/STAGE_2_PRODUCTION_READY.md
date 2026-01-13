# Stage 2 — Production Ready (Declaração de Maturidade)

**Status:** Declared (Stage 2)
**Date:** 2026-01-13
**Canonical Reference:** ADR 0021 — Product Roadmap and Maturity Stages (`docs/ADR/0021-product-roadmap-and-maturity-stages.md`)

Este documento formaliza que o repositório CONTRACTOR atende aos requisitos do **Stage 2 — Production Ready** conforme definido no **ADR 0021**.
Ele não introduz novas capacidades. Ele apenas referencia evidências já versionadas no repositório.

---

## 1) Escopo desta declaração

Esta declaração cobre exclusivamente os requisitos do **Stage 2** listados no ADR 0021:

- SLOs ativos
- Incident management
- Rollback completo
- SDKs estáveis
- Políticas de privacidade e retenção

---

## 2) Evidências por requisito (ADR 0021)

### 2.1 SLOs ativos

**Evidência (runbook):**
- `docs/RUNBOOKS/slo_active.md`

**Evidência (Prometheus rules/alerts):**
- `ops/prometheus/rules/contractor_slo_rules.yaml`
- `ops/prometheus/alerts/contractor_slo_alerts.yaml`

**Observação operacional:**
- Os serviços expõem métricas via `/metrics` (conforme runbook), e os SLOs são avaliados por queries PromQL e alertas versionados.

---

### 2.2 Incident Management

**Evidência (runbook):**
- `docs/RUNBOOKS/incident_management.md`

**Evidência (postmortem template):**
- `docs/incidents/_template.md`

**Observação operacional:**
- O processo é manual/semi-manual no Stage 2, com severidades mínimas (SEV-1/2/3), gatilhos por alertas e critérios de encerramento.

---

### 2.3 Rollback completo

**Evidência (runbook):**
- `docs/RUNBOOKS/rollback.md`

**Evidência complementar (release/promotion):**
- `docs/RUNBOOKS/release_promotion.md`

**Observação operacional:**
- Rollback Stage 2 é realizado via troca explícita do alias `current` para um `bundle_id` anterior válido, com validação pós-rollback.

---

### 2.4 SDKs estáveis

**Evidência (SDK Python mínimo):**
- `sdk/python/README.md`
- `sdk/python/pyproject.toml`
- `sdk/python/contractor_sdk/*`

**Observação de escopo (Stage 2):**
- O SDK é propositalmente mínimo (sem streaming, sem retries automáticos, sem cobertura completa de endpoints) e mantém contrato do payload canônico do runtime.

---

### 2.5 Políticas de privacidade e retenção

**Evidência (ADR de privacidade/retenção):**
- ADR 0018 — Data Privacy, LGPD/GDPR and Retention Policies (`docs/ADR/0018-data-privacy-lgpd-gdpr-and-retention-policies.md`)

**Evidência (documentos):**
- `docs/PRIVACY/data_inventory.md`
- `docs/PRIVACY/privacy_policy.md`
- `docs/PRIVACY/retention_policy.md`

**Evidência (runbook operacional):**
- `docs/RUNBOOKS/privacy_retention.md`

**Evidência (config canônica de defaults):**
- `ops/observability/retention.yaml`

**Observação operacional:**
- Stage 2 mantém retenção manual/semi-manual, com cache efêmero (TTL) e responsabilidades explícitas entre plataforma (processor) e tenant (controller), conforme ADR 0018.

---

## 3) Critérios de verificação local (evidência executável)

Os seguintes passos são referências operacionais já descritas nos runbooks. Esta seção apenas consolida:

1. Validar health checks:
   - Runtime: `GET /api/v1/runtime/healthz`
   - Control: `GET /api/v1/control/healthz`

2. Executar smoke test:
   - `./scripts/dev/smoke.sh`

3. Validar métricas:
   - Runtime: `GET /metrics` em `:8000`
   - Control: `GET /metrics` em `:8001`

4. Validar rollback (quando aplicável):
   - Seguir `docs/RUNBOOKS/rollback.md` para reatribuir alias `current` e validar resolução.

---

## 4) Limitações explícitas do Stage 2

Esta declaração **não** afirma capacidades do Stage 3 (Enterprise Ready). Em particular, Stage 2:

- Não inclui runtime dedicado por tenant.
- Não inclui automação completa de incidentes/on-call 24x7.
- Não inclui compliance/auditoria enterprise completa.
- Não inclui criptografia por tenant, data residency multi-região ou DLP/eDiscovery.
- Não inclui marketplace/ecossistema (Stage 4).

---

## 5) Declaração final

Com base nas evidências acima, o repositório CONTRACTOR está **formalmente declarado** como atendendo aos requisitos do **Stage 2 — Production Ready**, conforme ADR 0021.

Qualquer avanço para **Stage 3 — Enterprise Ready** deve seguir os critérios do ADR 0021 e a governança de ADRs do repositório, sem “pular estágio”.
