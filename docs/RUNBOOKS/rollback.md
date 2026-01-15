# Runbook — Rollback completo (Stage 2 / ADR 0021)

Este runbook formaliza o **rollback completo** exigido no Stage 2 pelo ADR 0021
(`docs/ADR/0021-product-roadmap-and-maturity-stages.md`). Ele descreve como
reverter o sistema para um estado funcional anterior usando **os mecanismos já
existentes** (bundles versionados + aliases `draft/candidate/current` + quality gates).
Não introduz automação nova.

> **Integração com Incident Management:** para SEV-1, rollback é a ação padrão de
> mitigação. Consulte `docs/RUNBOOKS/incident_management.md`.

## 1) Definição de rollback no CONTRACTOR

Rollback completo significa **reverter o bundle ativo** (alias `current`) de um
tenant para um **bundle anterior válido**, mantendo a consistência operacional
entre Control Plane e Runtime. O rollback é **manual** no Stage 2 e ocorre por
meio da **troca explícita do alias `current`** para um `bundle_id` anterior.

## 1.1) No Automatic Rollback

- Rollback é **sempre manual e auditável** por meio da troca explícita do alias `current`.
- **Não existe auto-rollback** no baseline atual.
- **Não existe mecanismo** que reverta automaticamente para bundle anterior sem ação humana.

## 2) Escopo do rollback

### O que entra no rollback (rollbackável)

- **Bundles de artefatos versionados** no registry (`registry/tenants/<tenant>/bundles/<bundle_id>`):
  - Ontologia, entidades e termos.
  - Policies (planner, cache, rate limit etc.).
  - Templates e suites de qualidade (quando presentes no bundle).
- **Aliases** `draft/candidate/current` por tenant, com rollback do `current`.

> Observação: o runtime sempre resolve `tenant_id + alias` para um `bundle_id`
> e executa apenas o bundle promovido; isso garante reversão determinística.

### O que NÃO entra no rollback (não rollbackável no Stage 2)

- **Dados persistidos de clientes** (ex.: bases externas, integrações, histórico).
- **Métricas, logs e audit logs** já emitidos.
- **Estado de execução** fora do bundle (cache externo, filas, etc.).

## 3) Quando executar rollback

- **Incidente SEV-1** (ação padrão de mitigação).
- Falha após promotion para `current`.
- Regressão funcional grave percebida em produção.

## 4) Pré-condições

- Bundle anterior disponível no registry.
- Sistema em estado consistente (Control Plane e Runtime saudáveis).
- Bundle anterior é válido (manifest ok) e já aprovado por gates básicos.

## 5) Passo a passo operacional (manual)

### 5.1 Identificar o bundle atual

```bash
curl -s http://localhost:8001/api/v1/control/tenants/<tenant_id>/resolve/current | jq
```

### 5.2 Identificar um bundle anterior válido

- Use histórico de promotion, audit logs ou lista de bundles no registry.
- Opcional: validar o bundle anterior.

```bash
curl -s -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
  http://localhost:8001/api/v1/control/tenants/<tenant_id>/bundles/<bundle_id>/validate | jq
```

### 5.3 Executar rollback do alias `current`

```bash
curl -s -X POST -H "Content-Type: application/json" \
  -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
  -d '{"bundle_id":"<bundle_id_anterior>"}' \
  http://localhost:8001/api/v1/control/tenants/<tenant_id>/aliases/current | jq
```

> Alternativa: o endpoint `/versions/{alias}` também funciona, mas `aliases/*`
> é o caminho recomendado por aplicar gates de qualidade.

⚠️ Executar rollback fora de janelas de pico quando possível.

### 5.4 Validar resolução do alias após rollback

```bash
curl -s http://localhost:8001/api/v1/control/tenants/<tenant_id>/versions/current/resolve | jq
```

## 6) Validação pós-rollback

- Health checks:
  - Control Plane: `/api/v1/control/healthz`
  - Runtime: `/api/v1/runtime/healthz`
- Smoke test: `scripts/dev/smoke.sh`
- Confirmar ausência de alertas críticos (SLOs/SEV-1).

## 7) Registro

- Atualizar o incidente com data/hora e bundle revertido.
- Referenciar rollback no postmortem (`docs/incidents/`).

## 8) Estado atual e limitações (Stage 2)

- Rollback é **manual** (sem automação de rollback baseada em métricas).
- Rollback **não afeta dados persistidos** ou métricas históricas.
- Rollback automático/avançado (canary, multi-região, feature flags) é Stage 3+.
