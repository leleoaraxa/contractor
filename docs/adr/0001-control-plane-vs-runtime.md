# ADR 0001 — Separação Control Plane vs Runtime

## Contexto
Sistemas de IA em produção exigem governança, previsibilidade e rastreabilidade.
Misturar controle e execução gera risco operacional.

## Opções consideradas
- Control Plane e Runtime acoplados
- Control Plane e Runtime separados

## Decisão
Separar explicitamente Control Plane e Runtime.

## Consequências
- Maior complexidade inicial
- Forte ganho em segurança, auditabilidade e escala
- Possibilidade de múltiplos runtimes governados
