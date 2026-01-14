# Runbook — SLA Violation / Risk (Stage 3 Enterprise)

## 1) Purpose / Scope

**Purpose:** responder a risco real de violação de SLA ou violação confirmada para runtime dedicado de tenant enterprise. Alinhado ao ADR 0025 e ADR 0023.

**In scope:** disponibilidade mensal abaixo do target, latência p95 mensal acima do limite, burn acelerado de budget de erro. **Out of scope:** incidentes de segurança sem impacto operacional (use `suspected_breach.md`).

## 2) Definitions (SEV-1..SEV-4)

Baseado no ADR 0025:

- **SEV-1:** violação imediata de SLA (ou indisponibilidade crítica).
- **SEV-2:** risco alto de violação de SLA (burn acelerado).
- **SEV-3:** degradação limitada sem risco imediato.
- **SEV-4:** evento informativo.

## 3) Triggers (Tenant-Level Observability)

Métricas por tenant (ADR 0024):

- **Disponibilidade mensal abaixo do target (SLA breach):**
  ```promql
  1 - (
    sum(increase(contractor_http_requests_total{service="runtime", path="/api/v1/runtime/ask", status_code=~"5..", tenant_id="<tenant_id>"}[30d]))
    /
    sum(increase(contractor_http_requests_total{service="runtime", path="/api/v1/runtime/ask", tenant_id="<tenant_id>"}[30d]))
  ) < 0.999
  ```
- **Latência p95 mensal acima do contrato:**
  ```promql
  histogram_quantile(0.95,
    sum(rate(contractor_http_request_duration_seconds_bucket{service="runtime", path="/api/v1/runtime/ask", tenant_id="<tenant_id>"}[30d])) by (le)
  ) > <contract_p95_seconds>
  ```
- **Burn rate acelerado (risco de violação):**
  ```promql
  (
    sum(rate(contractor_http_requests_total{service="runtime", path="/api/v1/runtime/ask", status_code=~"5..", tenant_id="<tenant_id>"}[5m]))
    /
    sum(rate(contractor_http_requests_total{service="runtime", path="/api/v1/runtime/ask", tenant_id="<tenant_id>"}[5m]))
  ) > <error_budget_burn_threshold>
  ```

## 4) Immediate Actions (mitigation first / no silent failures)

1. **Confirmar risco/violação** com métricas agregadas do tenant.
2. **Classificar SEV** (SEV-1 para violação confirmada; SEV-2 para risco real).
3. **Mitigar imediatamente:**
   - rollback de bundle recente (ADR 0022),
   - ajuste de capacidade do runtime dedicado,
   - redução de carga com rate limit por tenant.
4. **Registrar início do incidente** com timestamp e métricas iniciais.

## 5) Escalation Matrix (ADR 0025)

| SEV | Notificação | Prazo | Quem aciona | Quem é acionado |
| --- | --- | --- | --- | --- |
| SEV-1 | Imediata | 0–5 min | Operação | Engenharia + Liderança + Comercial/CS |
| SEV-2 | Até 30 min | 0–30 min | Operação | Engenharia + Produto/CS |
| SEV-3 | Até 4h | 0–4h | Operação | Engenharia |
| SEV-4 | Best effort | — | Operação | Engenharia (se necessário) |

## 6) Customer Communication (templates)

**Status inicial:**
> Identificamos risco de violação de SLA para o tenant **<tenant_id>**. Mitigação já iniciada. Próxima atualização em **<30 min>**.

**Atualização periódica:**
> Seguimos mitigando o risco de SLA. Métricas atuais: **<disponibilidade/latência>**. Ações em andamento: **<ação>**. Próxima atualização em **<30–60 min>**.

**Encerramento:**
> As métricas do tenant **<tenant_id>** retornaram ao patamar contratual desde **<timestamp>**. Seguiremos com postmortem e relatório sanitizado.

## 7) Evidence & Logging (ADR 0018)

Coletar evidências agregadas:

- disponibilidade/latência por tenant (sem payload)
- timestamps de detecção/mitigação/estabilização
- ações executadas (rollback, ajuste de capacidade)
- logs estruturados com IDs e status codes

## 8) Rollback & Recovery (ADR 0022)

Quando aplicar rollback:

- início do burn após deploy de bundle
- mitigação sem rollback não estabiliza rapidamente

Passos:

1. validar versão anterior no control plane
2. executar rollback manual (`docs/RUNBOOKS/rollback.md`)
3. validar métricas por tenant
4. registrar versão e horário

## 9) Postmortem (ADR 0025)

Obrigatório para:

- **SEV-1**
- **SEV-2 com impacto mensurável**

Template: `docs/incidents/_template.md` (versão sanitizada). Incluir linha do tempo, impacto no SLA e ações preventivas.

## 10) SLA Accounting (ADR 0023)

- **SLA clock** corre para SEV-1 e SEV-2.
- Métrica oficial: disponibilidade mensal e latência p95 mensal por tenant.
- Excluir janelas de manutenção previamente comunicadas.
- Evidências são imutáveis após fechamento.

## 11) Checklist

- [ ] Confirmar métricas de SLA por tenant
- [ ] Classificar SEV (1–4)
- [ ] Mitigar imediatamente (rollback/capacidade/rate limit)
- [ ] Notificar responsáveis conforme matriz de escalonamento
- [ ] Comunicar cliente com updates regulares
- [ ] Registrar evidências sem payload
- [ ] Validar estabilidade por janela mínima
- [ ] Executar postmortem quando aplicável
- [ ] Registrar impacto em SLA
