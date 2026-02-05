# Architecture Decision Records — CONTRACTOR

Este diretório contém os **Architecture Decision Records (ADRs)** do projeto CONTRACTOR.

Os ADRs registram decisões arquiteturais relevantes, seu contexto, alternativas consideradas
e consequências. Eles são **fonte de verdade** e têm precedência sobre código, comentários
ou implementações ad-hoc.

---

## ADRs existentes

| ID   | Título                                                                 | Status   |
|------|------------------------------------------------------------------------|----------|
| 0001 | Separação Control Plane vs Runtime                                     | Accepted |
| 0002 | Bundles imutáveis, identificação e compatibilidade                     | Accepted |
| 0003 | Modelo de aliases por tenant                                           | Accepted |
| 0004 | Auditoria mínima obrigatória                                           | Accepted |
| 0005 | Modelo mínimo de bundle                                                | Accepted |
| 0006 | API mínima do Control Plane                                            | Accepted |
| 0007 | Contrato mínimo do Runtime                                             | Accepted |
| 0008 | Compatibilidade e upgrade do Runtime                                   | Accepted |
| 0009 | Caso de uso modelo (FAQ determinístico demo)                           | Accepted |
| 0010 | Integração Runtime ↔ Control Plane                                     | Accepted |
| 0011 | Autenticação e autorização v1 (Control Plane)                          | Accepted |
| 0012 | Autenticação v1 do Runtime (chaves por tenant e validação de headers)  | Accepted |
| 0013 | Rate limiting e quotas (policy-driven)                                 | Accepted |
| 0014 | Auditoria end-to-end (formato, correlação e retenção mínima)           | Accepted |
| 0017 | Distribuição de bundles para o Runtime (fetch, digest e cache local) | Accepted |

---

## ADRs planejados (roadmap inevitável)

| ID   | Título                                                                 | Status | Motivo |
|------|------------------------------------------------------------------------|--------|--------|
| 0015 | Armazenamento de bundles no Control Plane (integridade e lifecycle)    | Draft  | ADR 0002/0005 exigem imutabilidade; falta definir storage real e GC. |
| 0016 | Quality gates v1 (suites, execução e critérios de promoção)            | Draft  | ADR 0005/0006/0009 dependem de gates explícitos para promoção. |
| 0018 | Observabilidade v1 (métricas mínimas, tracing e logs estruturados)      | Draft  | ADR 0004 exige sinais operacionais; precisa virar contrato mínimo. |
| 0019 | Promoção e rollback v1 (workflow de aliases e invariantes)             | Draft  | ADR 0003 define aliases, mas não formaliza o workflow de promoção e rollback. |


> Nota: os ADRs 0015–0019 são mantidos como **Draft** e devem existir como arquivos neste diretório
> enquanto estiverem em progresso, para evitar “roadmap sem documentação”.


---

## Ordem recomendada de implementação

1. **ADR 0016** — Quality gates v1
2. **ADR 0019** — Promoção e rollback v1 (workflow de aliases e invariantes)
3. **ADR 0015** — Armazenamento de bundles no Control Plane
4. **ADR 0018** — Observabilidade v1

---

## Regras

- Toda decisão estrutural relevante **exige um ADR**.
- ADRs são **imutáveis após Accepted** (mudanças exigem novo ADR).
- Implementações devem referenciar explicitamente o ADR correspondente.
- ADRs em progresso devem ser marcados como `Draft`.

---

## Fluxo

1. Criar ADR como `Draft`
2. Revisar decisão
3. Marcar como `Accepted`
4. Atualizar `docs/STATUS.md` se a decisão impactar milestone ou próxima tarefa
