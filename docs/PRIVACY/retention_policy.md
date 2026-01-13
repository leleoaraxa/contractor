# Política de retenção (Stage 2) — ADR 0021

> Referência: ADR 0021 — Product roadmap e maturity stages.

## Objetivo
Estabelecer defaults mínimos de retenção para Stage 2 (Production Ready), com operação manual/semi-manual.

## Retenção padrão por tipo
- **Logs de aplicação (stdout)**: 30 dias (default recomendado).
- **Audit logs (registry/control_plane/audit.log)**: 90 dias (default recomendado).
- **Métricas Prometheus**: 30 dias (default recomendado).
- **Traces**: 7 dias (se habilitados futuramente).
- **Bundles/artefatos (registry)**: retenção **indefinida** (imutáveis por design); remoções só via procedimento de governança.
- **Cache runtime (Redis/in-memory)**: TTL conforme policy (default curto); sem retenção de longo prazo.

## Critérios de purge
- Expiração por tempo (TTL) em cache e métricas.
- Rotação/remoção periódica de logs conforme política do operador.
- Audit logs podem ser truncados/apagados após o período definido, mantendo evidência mínima exigida.

## Procedimento operacional
- A retenção é **manual/semi-manual** no Stage 2.
- Deve haver evidência registrável de:
  - configuração de retenção (Prometheus/log driver)
  - data/resultado das rotinas de purge
  - justificativa de exceções

## Limitações (Stage 2)
- Não há automação completa de lifecycle management.
- Não há criptografia por tenant nem data residency multi-região.
