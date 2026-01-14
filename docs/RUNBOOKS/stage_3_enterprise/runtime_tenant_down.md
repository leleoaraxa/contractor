# Runbook — Runtime Tenant Down (Stage 3 Enterprise)

## 1) Purpose / Scope

**Purpose:** orientar resposta rápida quando o **runtime dedicado de um tenant** estiver indisponível (total ou parcial). O foco é **mitigação imediata**, comunicação contratual e evidências auditáveis para SLA. Alinhado ao ADR 0025 e ADR 0023.

**In scope:** indisponibilidade do runtime dedicado, erros 5xx sustentados, timeout em `/api/v1/runtime/ask` por tenant. **Out of scope:** falhas do Control Plane (não cobertas por SLA), incidentes de segurança (use `suspected_breach.md`).

## 2) Definitions (SEV-1..SEV-4)

Baseado no ADR 0025:

- **SEV-1:** runtime dedicado indisponível ou SLA em violação imediata.
- **SEV-2:** degradação relevante com risco de SLA.
- **SEV-3:** degradação limitada sem risco imediato.
- **SEV-4:** evento informativo sem impacto.

## 3) Triggers (Tenant-Level Observability)

Métricas por tenant (ADR 0024) **rotuladas por `tenant_id`**. Exemplos:

- **Disponibilidade abaixo do target (SLA):**
  ```promql
  1 - (
    sum(rate(runtime_tenant_http_requests_total{tenant_id="<tenant_id>", status_code=~"5.."}[5m]))
    /
    sum(rate(runtime_tenant_http_requests_total{tenant_id="<tenant_id>"}[5m]))
  ) < 0.999
  ```
- **Error rate sustentado (5xx) por tenant:**
  ```promql
  sum(rate(runtime_tenant_http_requests_total{tenant_id="<tenant_id>", status_code=~"5.."}[5m]))
  /
  sum(rate(runtime_tenant_http_requests_total{tenant_id="<tenant_id>"}[5m]))
  > 0.01
  ```
- **Latência p95 acima do contrato:**
  ```promql
  quantile_over_time(0.95,
    runtime_tenant_http_request_latency_seconds{tenant_id="<tenant_id>", status_code=~"2.."}[5m]
  ) > <contract_p95_seconds>
  ```

**Sinais adicionais (sem payload):** spikes de 5xx, saturação de CPU/memória do runtime dedicado, falhas de health check do runtime.

## 4) Immediate Actions (mitigation first / no silent failures)

1. **Confirmar o impacto por tenant** (5xx/timeout/latência) e classificar SEV.
2. **Mitigação imediata:**
   - reiniciar runtime dedicado (se aplicável e seguro),
   - reduzir carga ou bloquear tráfego danoso (rate limit por tenant),
   - **rollback** do bundle do tenant (ver ADR 0022 e [docs/RUNBOOKS/rollback.md](../rollback.md)).
3. **Registrar início do incidente** (timestamp, tenant_id, SEV, sintomas).
4. **Comunicar internamente** operação/engenharia (não aguardar root cause).

## 5) Escalation Matrix (ADR 0025)

| SEV | Notificação | Prazo | Quem aciona | Quem é acionado |
| --- | --- | --- | --- | --- |
| SEV-1 | Imediata | 0–5 min | Operação | Engenharia + Liderança técnica + Comercial/CS |
| SEV-2 | Até 30 min | 0–30 min | Operação | Engenharia + Produto/CS |
| SEV-3 | Até 4h | 0–4h | Operação | Engenharia |
| SEV-4 | Best effort | — | Operação | Engenharia (se necessário) |

## 6) Customer Communication (templates)

**Status inicial (SEV-1/SEV-2):**
> Detectamos indisponibilidade no runtime dedicado do tenant **<tenant_id>**. Nossa equipe já está em mitigação. Próxima atualização em **<30 min>**. Nenhum dado sensível é compartilhado por este canal.

**Atualização periódica:**
> Seguimos mitigando o incidente. Impacto atual: **<percentual de erro/latência>**. Medidas em andamento: **<ação executada>**. Próxima atualização em **<30–60 min>**.

**Encerramento:**
> O runtime dedicado do tenant **<tenant_id>** está estável desde **<timestamp>**. Seguiremos com postmortem e compartilharemos relatório sanitizado conforme contrato.

## 7) Evidence & Logging (ADR 0018)

Coletar **apenas** evidências técnicas **sem payload**:

- métricas agregadas por tenant (`tenant_id`, status codes, latência p95/p99)
- timestamps de detecção/mitigação/estabilização
- mudanças executadas (rollback, reinício, rate limit)
- logs estruturados **sem conteúdo de requisição** (IDs, status, duração)

## 8) Rollback & Recovery (ADR 0022)

Aplicar rollback quando:

- falha iniciou após deploy de bundle do tenant
- mitigação sem rollback não estabilizou em tempo adequado

Passos mínimos:

1. confirmar versão anterior está disponível no control plane
2. executar rollback manual conforme [docs/RUNBOOKS/rollback.md](../rollback.md)
3. validar health check e métricas por tenant
4. registrar versão revertida e horário

## 9) Postmortem (ADR 0025)

Obrigatório para:

- **SEV-1**
- **SEV-2 com impacto mensurável**

Template mínimo: [docs/incidents/_template.md](../../incidents/_template.md) (versão sanitizada). Incluir linha do tempo, impacto (SLA), causa raiz e ações corretivas.

## 10) SLA Accounting (ADR 0023)

- **SLA clock** corre para SEV-1 e SEV-2.
- Métrica oficial: disponibilidade mensal do runtime dedicado e latência p95 por tenant.
- Evidências são **imutáveis** após fechamento do incidente.
- Excluir janelas de manutenção previamente comunicadas.

## 11) Checklist

- [ ] Confirmar tenant_id e impacto em `/api/v1/runtime/ask`
- [ ] Classificar SEV (1–4) com base em métricas
- [ ] Iniciar mitigação imediata (rollback/restart/rate limit)
- [ ] Notificar responsáveis conforme matriz de escalonamento
- [ ] Comunicar cliente (status inicial + updates)
- [ ] Registrar evidências (sem payload)
- [ ] Confirmar estabilidade por janela mínima
- [ ] Executar postmortem quando aplicável
- [ ] Registrar impacto em SLA
