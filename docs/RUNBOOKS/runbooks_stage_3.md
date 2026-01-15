# Runbooks — Índice e completude (Stage 3)

## Inventário de runbooks relevantes

- `docs/RUNBOOKS/incident_management.md` — processo de incidentes, severidades e postmortem.
- `docs/RUNBOOKS/rollback.md` — rollback manual e integração documental com incidentes.
- `docs/RUNBOOKS/privacy_retention.md` — privacidade, retenção e limites de dados.
- `docs/RUNBOOKS/slo_active.md` — definição operacional de SLOs ativos e consultas base.
- `docs/RUNBOOKS/troubleshooting.md` — diagnóstico rápido de problemas comuns.
- `docs/RUNBOOKS/release_promotion.md` — fluxo de promoção/lançamento.
- `docs/RUNBOOKS/runtime_pipeline.md` — pipeline operacional do runtime.

## Critério de “completude Stage 3” (auditável)

Para Stage 3, considera-se completo **apenas no escopo documental** quando existir:

1) **Runbooks críticos documentados e versionados** cobrindo incidentes, rollback, privacidade/retenção, SLOs e troubleshooting.
2) **Definições mínimas de severidade e comunicação** incluídas no runbook de incidentes (SEV-1 a SEV-4 + comunicação com cliente).
3) **Integração documental** entre incidentes e rollback (referências cruzadas claras).
4) **Declaração explícita de limites do Stage 3** (sem validação em produção e sem 24x7).

## Lacunas ainda abertas (não atendidas no Stage 3)

- Template padrão de comunicação com cliente (mensagens iniciais/updates/encerramento).
- Runbook específico para atualização de status público e canais externos.
- Evidência de execução/validação em produção enterprise.
