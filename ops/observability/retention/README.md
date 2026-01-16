# Stage 3: Retenção configurável por tenant/plano (camada declarativa)

Este diretório contém a camada declarativa de retenção por plano e por tenant para o Stage 3,
sem alterar os defaults globais definidos em `ops/observability/retention.yaml`.

## Hierarquia de precedência

1. **Tenant** (`tenants.example.yaml`)
2. **Plano** (`plans.yaml`)
3. **Defaults globais** (`ops/observability/retention.yaml`)

## Observações importantes

- **Sem enforcement automático:** estes arquivos são declarativos e não aplicam retenção por conta própria.
- **Produção fora do escopo:** esta camada é apenas evidência Stage 3 (non-prod).
- **Stage 4 fora do escopo:** não há qualquer automação ou integração com runtime/control plane.
