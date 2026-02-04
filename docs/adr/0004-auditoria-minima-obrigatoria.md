# ADR 0004 — Auditoria mínima obrigatória (Control Plane e Runtime)

## Contexto
Empresas que operam IA em produção precisam responder perguntas como:
- O que mudou?
- Quando mudou?
- Quem mudou?
- Qual versão estava ativa em um incidente?

Sem auditoria integrada à arquitetura, essas respostas se tornam imprecisas,
incompletas ou impossíveis.

## Opções consideradas
- Logs best-effort sem padronização
- Auditoria apenas no Control Plane
- Auditoria obrigatória no Control Plane e Runtime

## Decisão
O CONTRACTOR exige **auditoria mínima obrigatória** em dois níveis:

### Control Plane (change audit)
Eventos obrigatórios:
- publish_bundle
- gate_pass / gate_fail
- promote_alias
- rollback_alias
- alterações de configuração por tenant

Campos mínimos:
- event_type
- actor (usuário/serviço)
- tenant_id
- bundle_id (quando aplicável)
- timestamp
- correlacionador (request_id / trace_id)

### Runtime (execution audit)
Eventos obrigatórios:
- execução de request
- negação por política (ex.: rate limit)
- erro de compatibilidade
- erro interno de execução

Campos mínimos:
- tenant_id
- bundle_id
- request_id / trace_id
- entidade/rota resolvida
- status da execução
- tempos agregados

## Consequências
**Ganhos**
- Diagnóstico confiável de incidentes
- Compliance e governança por design
- Confiança institucional para ambientes enterprise
- Base sólida para observabilidade e métricas

**Custos**
- Overhead operacional (logs/eventos)
- Necessidade de política de retenção e redaction

**Regras explícitas**
- Auditoria não é opcional
- Eventos não auditados são considerados falha arquitetural
- Dados sensíveis devem ser tratados via policy (redaction)

**Fora do escopo**
- Análise comportamental avançada
- BI ou dashboards de negócio
