# Evidência — Dashboards dedicados por tenant (Stage 3, não produção)

## Objetivo
Documentar a entrega de dashboards Grafana dedicados por tenant, versionados no repositório, usando apenas métricas existentes do runtime (`runtime_tenant_*`).

## Escopo e restrições atendidas
- Nenhuma métrica nova criada.
- Nenhuma alteração em runtime/control plane.
- Somente arquivos novos adicionados ao repositório.
- Conteúdo voltado para uso não produtivo (nonprod).

## Artefatos entregues
- `ops/observability/dashboards/tenant/runtime_overview_tenant.json`
- `ops/observability/dashboards/tenant/runtime_http_tenant.json`
- `ops/observability/dashboards/tenant/README.md`

## Detalhes dos dashboards
- Variável `$tenant` baseada em `tenant_ref` via `label_values(runtime_tenant_http_requests_total, tenant_ref)`.
- Todas as queries filtram `tenant_ref="$tenant"`.
- Métricas usadas:
  - `runtime_tenant_http_requests_total`
  - `runtime_tenant_http_request_latency_seconds_bucket`

## Como validar (nonprod)
1. Importar os JSONs no Grafana conforme README.
2. Selecionar um `tenant_ref` válido na variável **Tenant**.
3. Verificar preenchimento dos painéis de taxa de requisições, erros e latência.
