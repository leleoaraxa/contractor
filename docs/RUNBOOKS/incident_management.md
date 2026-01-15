# Incident Management (Stage 2 / ADR 0021)

Este runbook documenta o processo de Incident Management exigido pelo **ADR 0021**
(`docs/ADR/0021-product-roadmap-and-maturity-stages.md`). Ele complementa os SLOs ativos
em `docs/RUNBOOKS/slo_active.md` e não altera a lógica de alertas existente.

## Definição de incidente no CONTRACTOR

Um incidente é qualquer evento operacional que resulte em:

- Violação ou risco iminente de violação de SLO (burn de budget).
- Indisponibilidade do runtime (`/api/v1/runtime/ask`) ou do control plane (`/api/v1/control/healthz`).
- Erro sistêmico no control plane que impeça operações críticas (ex.: deploys, health checks, gestão de bundles).

## Severidades (mínimo viável)

- **SEV-1**: runtime indisponível ou burn rápido crítico (fast burn) de SLOs essenciais.
- **SEV-2**: degradação relevante com burn lento (slow burn) dos SLOs.
- **SEV-3**: incidentes menores sem impacto direto em SLO (ex.: alarmes auxiliares, falhas intermitentes sem impacto).
- **SEV-4**: baixo impacto ou informativo, sem risco imediato de SLO/SLA (ex.: anomalias cosméticas, alertas de baixa relevância).

## Gatilhos de incidente (integração com alertas existentes)

Alertas Prometheus já versionados que disparam incidentes:

| Alerta | Origem | Severidade | Situação típica |
| --- | --- | --- | --- |
| `ContractorRuntimeAskSLOFastBurn` | `ops/prometheus/alerts/contractor_slo_alerts.yaml` | SEV-1 | Burn crítico do SLO do runtime (`/api/v1/runtime/ask`). |
| `ContractorControlHealthzSLOFastBurn` | `ops/prometheus/alerts/contractor_slo_alerts.yaml` | SEV-1 | Burn crítico do SLO do control (`/api/v1/control/healthz`). |
| `ContractorRuntimeAskSLOSlowBurn` | `ops/prometheus/alerts/contractor_slo_alerts.yaml` | SEV-2 | Burn lento do SLO do runtime. |
| `ContractorControlHealthzSLOSlowBurn` | `ops/prometheus/alerts/contractor_slo_alerts.yaml` | SEV-2 | Burn lento do SLO do control. |

Para entender os SLOs e as métricas usadas, consultar:
- Runbook de SLOs: `docs/RUNBOOKS/slo_active.md`
- Recording rules: `ops/prometheus/rules/contractor_slo_rules.yaml`

## Como confirmar o incidente (consulta de métricas)

Use PromQL conforme o runbook de SLOs. Exemplos úteis para confirmação:

**Erro 5xx recente (runtime /ask)**

```promql
sum(contractor:http_requests:rate5m{service="runtime", path="/api/v1/runtime/ask", status_code=~"5.."})
/
sum(contractor:http_requests:rate5m{service="runtime", path="/api/v1/runtime/ask"})
```

**Erro 5xx recente (control /healthz)**

```promql
sum(contractor:http_requests:rate5m{service="control", path="/api/v1/control/healthz", status_code=~"5.."})
/
sum(contractor:http_requests:rate5m{service="control", path="/api/v1/control/healthz"})
```

## Fluxo de resposta

1) **Detecção**
   - Alertas Prometheus (fast/slow burn) ou observação manual via métricas/logs.
2) **Confirmação**
   - Validar impacto (5xx, latência, indisponibilidade) e confirmar SLO em risco.
3) **Mitigação**
   - Ações de contenção (ex.: rollback manual, limitar tráfego, reiniciar serviço).
   - Escalar para engenharia responsável quando necessário.
4) **Comunicação (interna)**
   - Atualizar stakeholders internos com severidade, impacto e status.
5) **Encerramento**
   - Validar retorno à estabilidade e registrar postmortem mínimo.

## Customer Communication (Enterprise)

- **Quando comunicar:** SEV-1 e SEV-2. SEV-3 somente se houver impacto direto percebido pelo cliente.
- **O que comunicar:** status inicial, atualizações de progresso e encerramento; incluir link para postmortem sanitizado quando aplicável.
- **O que NÃO comunicar:** payload sensível, dados internos, chaves/segredos ou detalhes que exponham arquitetura interna.
- **Canal:** fora de escopo deste runbook (não fixa ferramenta/processo de envio).

## Critérios de encerramento

- Métricas retornaram ao patamar normal e SLO não está em burn crítico.
- Evidências de estabilidade por uma janela mínima (ex.: 30-60 min para SEV-1/SEV-2).
- Postmortem registrado em `docs/incidents/`.

## Postmortem mínimo

- Template obrigatório: `docs/incidents/_template.md`
- Local para salvar: `docs/incidents/YYYY-MM-DD-<slug>.md`
- Campos mínimos: resumo, impacto, linha do tempo, causa raiz, mitigação, ações preventivas, SLO afetado.

## Estado atual (Stage 2)

- Processo manual/semi-manual (documentado e operacional, sem automação completa).
- Ferramentas externas (PagerDuty/Opsgenie etc.) são consideradas para Stage 3.
- Não há on-call formal 24x7 neste estágio.
