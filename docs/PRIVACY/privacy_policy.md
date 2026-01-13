# Política de privacidade (Stage 2) — ADR 0021

> Referência: ADR 0021 — Product roadmap e maturity stages.

## Objetivo
Esta política define o que o sistema CONTRACTOR coleta, processa e **não** coleta no Stage 2 (Production Ready).

## O que coletamos
- **Dados de entrada do runtime**: `tenant_id`, `bundle_id`/`release_alias` e `question` enviados ao endpoint `/api/v1/runtime/ask`.
- **Metadados operacionais**: eventos de auditoria (mudanças de alias e execuções de quality) em `registry/control_plane/audit.log`.
- **Telemetria**: logs de aplicação (stdout) e métricas Prometheus (quando habilitadas).

## Finalidade (operacional / observability / quality)
- **Operação do runtime**: roteamento determinístico e execução do pipeline do `/ask`.
- **Observabilidade**: troubleshooting e acompanhamento de SLOs.
- **Qualidade**: rastreabilidade de promoções/execuções de suites (audit log).

## O que NÃO coletamos
- Não coletamos dados fora do contrato do runtime/control.
- Não coletamos dados de pagamento, documentos pessoais, nem perfis comportamentais.
- Não armazenamos payloads de request/resposta em bases externas obrigatórias.

## Dados sensíveis / PII
- **Proibido** registrar PII, credenciais ou segredos em logs e audit logs.
- O header `X-API-Key` **nunca** deve ser persistido.
- O operador do sistema é responsável por garantir que `question` não contenha PII sensível quando observabilidade estiver habilitada.

## Responsabilidades
- **Operador do sistema**: define e aplica retenção, purge e controles de acesso aos logs/métricas.
- **Equipe de produto**: mantém documentação atualizada e alinhada ao ADR 0021.

## Referências
- ADR 0021 — Product roadmap e maturity stages.
- ADR 0018 — Data privacy, LGPD/GDPR & retention policies.
