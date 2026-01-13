# SLOs ativos (Stage 2 / ADR 0021)

Este runbook implementa os SLOs ativos definidos no **ADR 0021** (`docs/ADR/0021-product-roadmap-and-maturity-stages.md`).

## Definições de SLO

Fonte de verdade dos targets efetivamente usados nos alertas: `ops/prometheus/rules/contractor_slo_rules.yaml` (metric `contractor:slo_error_budget{...}`). O arquivo `ops/observability/slo.yaml` é apenas referência documental.

| SLO | Serviço | Endpoint | Indicador | Janela | Target |
| --- | --- | --- | --- | --- | --- |
| SLO-1 | runtime | `/api/v1/runtime/ask` | disponibilidade (2xx/total) | 30d | 99.5% (configurável) |
| SLO-2 | control | `/api/v1/control/healthz` | disponibilidade (2xx/total) | 30d | 99.5% (configurável) |

## Onde ficam as rules e alertas

- Recording rules: `ops/prometheus/rules/contractor_slo_rules.yaml`
- Alert rules: `ops/prometheus/alerts/contractor_slo_alerts.yaml`

As métricas são expostas em:
- Runtime: `http://<runtime-host>:8000/metrics`
- Control: `http://<control-host>:8001/metrics`

## Como testar

1) Suba os serviços principais:

```bash
docker compose up -d --build
```

2) Verifique as métricas:

```bash
curl -s http://localhost:8000/metrics | head -n 20
curl -s http://localhost:8001/metrics | head -n 20
```

3) Execute queries PromQL (em Prometheus/Grafana):

**Disponibilidade 30d (runtime /ask)**

```promql
1 - (
  sum(contractor:http_requests:increase30d{service="runtime", path="/api/v1/runtime/ask", status_code=~"5.."})
  /
  sum(contractor:http_requests:increase30d{service="runtime", path="/api/v1/runtime/ask"})
)
```

**Disponibilidade 30d (control /healthz)**

```promql
1 - (
  sum(contractor:http_requests:increase30d{service="control", path="/api/v1/control/healthz", status_code=~"5.."})
  /
  sum(contractor:http_requests:increase30d{service="control", path="/api/v1/control/healthz"})
)
```

**Error rate (5m)**

```promql
sum(contractor:http_requests:rate5m{service="runtime", path="/api/v1/runtime/ask", status_code=~"5.."})
/
clamp_min(sum(contractor:http_requests:rate5m{service="runtime", path="/api/v1/runtime/ask"}), 1)
```

4) Execute os testes existentes:

```bash
./scripts/dev/smoke.sh
pytest -q tests/integration/test_e2e_flow.py
```

## Como interpretar alertas

Quando um alerta de burn dispara:

1) Verifique a taxa de 5xx no endpoint e o volume total de requests.
2) Confirme se há mudanças recentes no runtime/control (deploys, migrations, bundles).
3) Inspecione logs e dependências (Redis/Postgres) para identificar a origem do erro.
4) Se o problema for intermitente, acompanhe a janela longa (6h) para validar tendência.
5) Registre o impacto e proponha ajustes no target conforme histórico real.

## Pré-requisitos de stack

Este repositório ainda não versiona um serviço Prometheus/Grafana no `docker-compose.yml`. Para ativar os SLOs em ambiente real, é necessário montar os arquivos de rules e alertas em uma instância existente de Prometheus.
