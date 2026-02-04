# ADR 0007 — Contrato mínimo do Runtime

## Contexto
O Runtime é o componente responsável por **executar sistemas de IA em produção**
sob governança do Control Plane. Para preservar determinismo, auditabilidade,
segurança e isolamento multi-tenant, o Runtime deve operar com um **contrato mínimo,
explícito e restritivo**.

Sem um contrato claro:
- runtimes tendem a incorporar lógica de governança indevida,
- execuções se tornam não determinísticas,
- auditoria e rollback perdem confiabilidade,
- integrações com o Control Plane ficam implícitas e frágeis.

Este ADR define o **contrato mínimo do Runtime (v1)**, incluindo responsabilidades,
endpoints, payloads e integração obrigatória com o Control Plane.

## Opções consideradas
- Runtime com lógica de decisão e fallback próprios
- Runtime flexível com execução ad-hoc
- **Runtime mínimo, determinístico e governado por contrato (v1)**

## Decisão
Adotar um **Runtime mínimo**, com responsabilidades estritamente limitadas a:

- executar requests usando exclusivamente bundles promovidos (`current`),
- resolver bundles apenas via Control Plane,
- aplicar políticas determinísticas definidas em bundle/policy,
- emitir sinais completos de auditoria e observabilidade,
- **não** decidir, versionar ou promover comportamento.

O Runtime é um **executor governado**, não um orquestrador autônomo.

## Responsabilidades do Runtime

### O Runtime DEVE
- Expor endpoint(s) de execução do sistema governado.
- Resolver `tenant_id` e alias (`current`) para `bundle_id` via Control Plane.
- Executar pipeline definido no bundle de forma determinística.
- Aplicar políticas runtime declaradas (ex.: rate limiting).
- Emitir auditoria de execução e sinais operacionais.
- Rejeitar execuções fora de contrato (erro seguro).

### O Runtime NÃO DEVE
- Alterar bundles ou aliases.
- Executar bundles não promovidos.
- Inferir comportamento fora da ontologia/contratos.
- Introduzir lógica hardcoded de domínio.
- Manter estado mutável que altere resultados entre execuções.

## Endpoints mínimos (conceituais)

### Execução principal
- `POST /execute`
- Responsabilidade:
  - receber payload de execução,
  - identificar tenant autenticado,
  - resolver bundle `current`,
  - executar pipeline governado,
  - retornar resposta e metadados mínimos.

Payload mínimo (conceitual):
- `request_id`
- payload definido pelo bundle (ex.: `question`, `context`, etc.)

Resposta mínima:
- resultado do sistema governado,
- `bundle_id`
- `request_id`
- status da execução.

---

### Health check
- `GET /healthz`
- Responsabilidade:
  - indicar disponibilidade do runtime,
  - **não** validar governança ou bundles.

---

## Integração obrigatória com o Control Plane

### Resolução de bundle
- Runtime deve chamar:
  - `GET /tenants/{tenant_id}/resolve/current`
- Resultado usado como **única fonte de verdade** para execução.

Regras:
- Resolução pode ser cacheada (TTL curto e seguro).
- Cache inválido deve resultar em nova resolução.
- Runtime nunca assume `bundle_id` por conta própria.

---

### Auditoria de execução
Para cada execução, o Runtime deve emitir evento contendo:
- `tenant_id`
- `bundle_id`
- `request_id`
- alias resolvido (`current`)
- entidade/rota resolvida (se aplicável)
- status da execução
- tempos agregados
- erros (se houver)

Auditoria é **obrigatória**, não opcional.

## Segurança (v1)
Requisitos mínimos:
- Autenticação obrigatória por tenant.
- Isolamento lógico por tenant.
- Rate limiting aplicado conforme policy.
- Rejeição explícita de execuções inválidas ou incompatíveis.
- Redaction de dados sensíveis conforme policy.

Detalhes adicionais de segurança serão tratados em ADR específico.

## Compatibilidade e erro seguro
- Runtime deve validar compatibilidade do bundle com sua versão.
- Bundle incompatível → erro explícito e auditado.
- Falhas de resolução ou policy → erro seguro (fail closed).
- Runtime **não** tenta fallback silencioso.

## Consequências

### Ganhos
- Execução previsível e reproduzível
- Governança clara entre Control Plane e Runtime
- Base sólida para observabilidade e compliance
- Simplicidade operacional

### Custos
- Menor flexibilidade ad-hoc
- Dependência explícita do Control Plane

### Fora do escopo (v1)
- Execução de múltiplos bundles
- Fallback automático entre versões
- Execução sem Control Plane
- Customização de domínio por código

## Status
- Aprovado como contrato mínimo do Runtime (v1)
- Qualquer expansão exige novo ADR
