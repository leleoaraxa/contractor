# STATUS — CONTRACTOR

## Estado atual
- Tipo de produto: SaaS B2B (Control Plane para sistemas de IA governados)
- Fase: Fundação técnica
- Milestone atual: Núcleo arquitetural, contratos e demo canônica definidos

## O que já está decidido
- Separação explícita entre Control Plane e Runtime (ADR 0001)
- Bundles imutáveis com identificação/digest e compatibilidade com runtime (ADR 0002)
- Aliases por tenant (draft / candidate / current) para promoção e rollback (ADR 0003)
- Auditoria mínima obrigatória (ADR 0004)
- Arquitetura v1 documentada (ADR implícito)
- Modelo mínimo de bundle (ADR 0005)
- API mínima do Control Plane (ADR 0006)
- Contrato mínimo do Runtime (ADR 0007)
- Compatibilidade e upgrade do Runtime (ADR 0008)
- Caso de uso modelo oficial: FAQ determinístico (ADR 0009)
- Bundle de demo (FAQ determinístico) implementado conforme ADR 0009
- Testes E2E do Runtime (fluxo via alias config) implementados e validados no runner oficial (docker compose run --rm tests)
- Integração Runtime ↔ Control Plane para resolução do alias `current` via HTTP (fail-closed) implementada e validada conforme ADR 0010 (Accepted).
- Autenticação e autorização v1 do Control Plane (API key por tenant, tenant-aware e fail-closed) implementadas e validadas conforme ADR 0011 (Accepted).
- Autenticação v1 do Runtime (API key por tenant via `X-Tenant-Id` + `X-Api-Key`, sem tenant implícito e fail-closed para configuração inválida/ausente) implementada e validada conforme ADR 0012 (Accepted).
- Rate limiting e quotas policy-driven por tenant no Runtime (`POST /execute`), com fail-closed para policy ausente/inválida e resposta 429 com `Retry-After`, implementados e validados conforme ADR 0013 (Accepted).
- Auditoria end-to-end v1 (schema mínimo, correlação por `X-Request-Id`, sink configurável com fail-closed, retenção mínima e precedência de erro de auditoria) implementada e validada conforme ADR 0014 (Accepted).
- Distribuição de bundles para o Runtime (fetch, digest e cache local) implementada e validada conforme ADR 0017 (Accepted).
- Quality gates v1 mínimos no Control Plane (endpoints de execução/status/history, execução determinística de suites do bundle e persistência local com auditoria) implementados e validados conforme ADR 0016 (Draft).

## O que está em aberto
- Materialização completa do Control Plane como serviço/API governado (além do endpoint mínimo de resolução)
- Enforcement completo de políticas cross-cutting no Runtime
- Pipeline de promoção e rollback de bundles via aliases
- Observabilidade operacional mínima

## Última decisão relevante
- 2026-02-05: Aprovado e promovido o contrato de auditoria end-to-end v1, com correlação obrigatória, redaction explícito e fail-closed com precedência (ADR 0014).
- 2026-02-05: Aprovado e promovido o contrato de distribuição de bundles para o Runtime (ADR 0017).

## Próxima tarefa atômica
- Iniciar ADR 0016 (Quality gates v1).
