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

## O que está em aberto
- Estratégia de testes de integração end-to-end (CI)
- Implementação do bundle de demo (FAQ)
- Implementação do Runtime mínimo (executor demo)
- Plano de implementação incremental (PRs atômicas)

## Última decisão relevante
- 2026-02-04: Aprovado o caso de uso modelo oficial (FAQ determinístico) como demo canônica do CONTRACTOR (ADR 0009).

## Próxima tarefa atômica
- Implementar o **bundle de demo (FAQ determinístico)** conforme ADR 0009, incluindo:
  - dados (JSON),
  - ontologia,
  - schemas,
  - suites golden,
  - policies mínimas.
