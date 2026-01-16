# Evidência Stage 3 — Quality Gate rejeita suites stub (non-prod)

## Comportamento final

Suites marcadas como `stub` não são aceitas pelo promotion gate. Mesmo que o relatório de qualidade indique status `pass`, o gate falha se detectar resultados de suites stub, evitando overclaim de qualidade em Stage 3 non-prod.

## Racional

O ADR 0009 define que suites obrigatórias são **blocking** para promoção (`candidate`/`current`) e que a qualidade passa a ser contratual. Portanto, resultados de suites `stub` não podem ser tratados como aprovação válida do gate.

Referência: `docs/ADR/0009-quality-gates-and-release-promotion-criteria.md`.

## Como reproduzir

1. Execute os testes de integração (inclui o cenário de suites stub):

```bash
pytest -q tests/integration/test_promotion_gates.py
```

### Resultado esperado

O teste `test_promotion_gate_rejects_stub_suites` deve falhar o gate com erro `promotion_gate_failed` quando o relatório contém suite `stub`.
