# Contexto
<!-- 1–3 linhas: qual problema técnico/contrato isso resolve? Referencie ADRs/STATUS -->

- Milestone/STATUS: <!-- ex: Fundação técnica / ADR 0006 -->
- ADR(s): <!-- ex: ADR 0006, ADR 0005 -->
- Issue/Task: <!-- opcional -->

# O que mudou
<!-- bullets objetivos. Não explique “como”, explique “o que” -->
-
-

# Escopo e atomicidade
<!-- deixe explícito o que está dentro e o que está fora -->
**Dentro**
-

**Fora**
-

# Como testar
<!-- comandos e o que você espera ver -->
## Unit tests
- `pytest -q`

## Integration / smoke (se aplicável)
- `./scripts/dev/smoke.sh` (ou equivalente)
- Observações:

# Evidências
<!-- cole outputs curtos ou links; se muito grande, anexe -->
- Testes: PASS/FAIL
- Gates: PASS/FAIL (se existirem)
- Logs/metrics relevantes:

# Riscos e rollback
<!-- sempre presente, mesmo que “baixo” -->
## Riscos
-

## Rollback
- Estratégia: <!-- ex: reverter PR / rollback alias current -> previous -->
- Impacto esperado do rollback:

# Checklist DoD
- [ ] Alinhado ao PRODUCT.md (sem escopo de produto/UX indevido)
- [ ] Não adiciona lógica hardcoded de domínio
- [ ] Mudança é determinística e auditável
- [ ] Testes adicionados/atualizados e passando
- [ ] Documentação atualizada (STATUS.md / ADR / ARCHITECTURE.md quando aplicável)
