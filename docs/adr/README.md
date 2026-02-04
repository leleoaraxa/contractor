# Architecture Decision Records — CONTRACTOR

Este diretório contém os **Architecture Decision Records (ADRs)** do projeto CONTRACTOR.

Os ADRs registram decisões arquiteturais relevantes, seu contexto, alternativas consideradas e consequências.
Eles são **fonte de verdade** e têm precedência sobre código, comentários ou implementações ad-hoc.

## ADRs existentes

| ID   | Título                                             | Status   |
|------|----------------------------------------------------|----------|
| 0001 | Separação Control Plane vs Runtime                 | Accepted |
| 0002 | Bundles imutáveis, identificação e compatibilidade | Accepted |
| 0003 | Modelo de aliases por tenant                       | Accepted |
| 0004 | Auditoria mínima obrigatória                       | Accepted |
| 0005 | Modelo mínimo de bundle                            | Accepted |
| 0006 | API mínima do Control Plane                        | Accepted |
| 0007 | Contrato mínimo do Runtime                         | Accepted |
| 0008 | Compatibilidade e upgrade do Runtime               | Accepted |
| 0009 | Caso de uso modelo (FAQ determinístico demo)       | Accepted |

## Regras
- Toda decisão estrutural relevante **exige um ADR**.
- ADRs são **imutáveis após Accepted** (mudanças exigem novo ADR).
- Implementações devem referenciar o ADR correspondente.
- ADRs em progresso devem ser marcados como `Draft`.

## Fluxo
1. Criar ADR como `Draft`
2. Revisar decisão
3. Marcar como `Accepted`
4. Atualizar `docs/STATUS.md` se a decisão impactar milestone ou próxima tarefa
