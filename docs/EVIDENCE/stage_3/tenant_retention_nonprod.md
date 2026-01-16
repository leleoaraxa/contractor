# Evidência Stage 3 — Retenção por tenant/plano (non-prod)

## Escopo

- Stage 3 (camada declarativa) para retenção configurável por tenant/plano.
- Aplicável apenas a ambientes non-prod.

## Referência aos defaults globais

Os defaults globais de retenção permanecem em `ops/observability/retention.yaml` (Stage 2) e não são alterados.

## Camada por plano e por tenant

- **Planos:** definidos em `ops/observability/retention/plans.yaml`, estendendo (nunca reduzindo) os defaults globais.
- **Tenants (exemplos):** definidos em `ops/observability/retention/tenants.example.yaml`, mapeando tenants fictícios para planos.

## Limitações

- **Sem produção:** esta evidência não contempla produção.
- **Sem automação/enforcement:** não há aplicação automática de retenção.
- **Sem mudanças em runtime/control plane:** apenas camada declarativa Stage 3.
