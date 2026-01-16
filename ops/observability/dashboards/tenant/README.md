# Dashboards de runtime por tenant (Stage 3)

## Propósito
Este diretório contém dashboards Grafana versionados para observabilidade do runtime por tenant, atendendo ao ADR 0028 (Stage 3). Eles ajudam a visualizar o desempenho e a saúde de um tenant específico sem criar métricas novas.

## Métricas usadas
Os dashboards usam somente métricas existentes do runtime com prefixo `runtime_tenant_*`:
- `runtime_tenant_http_requests_total`
- `runtime_tenant_http_request_latency_seconds_bucket`

Todas as consultas filtram o label `tenant_id` com a variável `$tenant`.

## Como importar no Grafana
1. Acesse **Dashboards → New → Import**.
2. Faça upload de um dos arquivos JSON deste diretório:
   - `runtime_overview_tenant.json`
   - `runtime_http_tenant.json`
3. Selecione o datasource Prometheus usado para métricas do runtime.
4. Salve o dashboard. A variável **Tenant** ficará disponível para selecionar o `tenant_id` desejado.
