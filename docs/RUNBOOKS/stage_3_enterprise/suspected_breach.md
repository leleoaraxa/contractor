# Runbook — Suspected Breach / Segurança (Stage 3 Enterprise)

## 1) Purpose / Scope

**Purpose:** responder a indícios de breach, acesso não autorizado ou exfiltração potencial em tenants enterprise, mantendo evidências auditáveis e comunicação contratual. Alinhado ao ADR 0025 e ADR 0018.

**In scope:** eventos suspeitos de segurança relacionados ao runtime dedicado, credenciais, acessos anômalos, alteração inesperada de configurações do tenant. **Out of scope:** incidentes puramente de disponibilidade sem componente de segurança (use `runtime_tenant_down.md`).

## 2) Definitions (SEV-1..SEV-4)

Baseado no ADR 0025:

- **SEV-1:** evidência de acesso não autorizado confirmado ou vazamento provável.
- **SEV-2:** suspeita forte de breach com sinais persistentes.
- **SEV-3:** alerta de segurança com baixa confiança.
- **SEV-4:** evento informativo (ex.: teste interno documentado).

## 3) Triggers (Tenant-Level Observability)

Métricas e sinais auditáveis (ADR 0024), **sem payload**:

- **Picos anômalos de autenticação falha** por tenant:
  ```promql
  sum(rate(contractor_auth_failures_total{tenant_id="<tenant_id>"}[5m])) > <baseline_threshold>
  ```
- **Aumento abrupto de requisições** fora do padrão de uso:
  ```promql
  sum(rate(contractor_http_requests_total{service="runtime", tenant_id="<tenant_id>"}[5m]))
  > <baseline_multiplier>
  ```
- **Mudanças administrativas inesperadas** (logs de auditoria):
  - rotação de credenciais fora de janela
  - criação de tokens fora de processo

## 4) Immediate Actions (mitigation first / no silent failures)

1. **Classificar SEV** e acionar equipe de segurança/engenharia imediatamente para SEV-1/2.
2. **Conter o impacto:**
   - revogar credenciais suspeitas,
   - bloquear tokens, IPs ou origens maliciosas,
   - isolar o runtime dedicado do tenant se necessário.
3. **Preservar evidências** (logs estruturados, métricas agregadas, timestamps).
4. **Comunicar internamente** (segurança, liderança técnica, jurídico/comercial quando aplicável).

## 5) Escalation Matrix (ADR 0025)

| SEV | Notificação | Prazo | Quem aciona | Quem é acionado |
| --- | --- | --- | --- | --- |
| SEV-1 | Imediata | 0–5 min | Operação/Segurança | Engenharia + Liderança + Jurídico/Comercial |
| SEV-2 | Até 30 min | 0–30 min | Operação/Segurança | Engenharia + Liderança |
| SEV-3 | Até 4h | 0–4h | Operação/Segurança | Engenharia |
| SEV-4 | Best effort | — | Operação/Segurança | Engenharia (se necessário) |

## 6) Customer Communication (templates)

**Status inicial:**
> Identificamos um evento de segurança em investigação para o tenant **<tenant_id>**. A contenção foi iniciada e manteremos atualizações periódicas. Nenhum dado sensível será compartilhado por este canal.

**Atualização periódica:**
> A investigação segue em andamento. Medidas executadas: **<ação>**. Impacto observado: **<descrição agregada>**. Próxima atualização em **<30–60 min>**.

**Encerramento:**
> Encerramos a investigação inicial do evento de segurança para o tenant **<tenant_id>**. O relatório sanitizado e evidências agregadas serão disponibilizados conforme contrato.

## 7) Evidence & Logging (ADR 0018)

Coletar **apenas** evidências sem payload:

- IDs de eventos, timestamps, tenant_id
- métricas agregadas (rate, status codes, volume)
- logs de auditoria (alterações administrativas)
- hashes ou IDs de artefatos de configuração (sem conteúdo)

## 8) Rollback & Recovery (ADR 0022)

Aplicar rollback quando:

- breach associado a bundle recém-publicado
- correções exigirem retorno imediato a versão anterior

Passos mínimos:

1. validar versão anterior no control plane
2. executar rollback manual (`docs/RUNBOOKS/rollback.md`)
3. revalidar isolamento do runtime dedicado
4. registrar versão revertida e horário

## 9) Postmortem (ADR 0025)

Obrigatório para:

- **SEV-1**
- **SEV-2 com impacto mensurável**

Template: `docs/incidents/_template.md` (versão sanitizada). Incluir causa raiz, impacto, ações corretivas e timeline.

## 10) SLA Accounting (ADR 0023)

- SLA clock **só corre** se houver impacto mensurável na disponibilidade/latência do runtime dedicado.
- Incidentes puramente de segurança sem impacto operacional **não contam** para SLA.
- Evidências devem ser preservadas e imutáveis após encerramento.

## 11) Checklist

- [ ] Confirmar sinais de segurança por tenant (sem payload)
- [ ] Classificar SEV e iniciar contenção imediata
- [ ] Revogar credenciais / bloquear origens suspeitas
- [ ] Preservar evidências (logs/metrics)
- [ ] Notificar responsáveis conforme matriz de escalonamento
- [ ] Comunicar cliente com updates regulares
- [ ] Validar estabilidade e encerramento
- [ ] Executar postmortem quando aplicável
- [ ] Registrar impacto (ou não) em SLA
