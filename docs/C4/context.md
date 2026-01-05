## Contexto (C4 - Nível 1)

CONTRACTOR é composto por um **Control Plane** (governança de bundles) e um **Runtime** (execução de /ask) que compartilham apenas artefatos versionados em um **Registry** baseado em filesystem no Stage 0. Redis está provisionado apenas como placeholder para futuras capacidades de cache/quotas (ADR-0008, ADR-0013).

```mermaid
graph TD
  User[DevOps / Tenant Admin] -->|CRUD Tenants & Bundles| ControlPlaneAPI
  AppUser[Runtime Client (/ask)] -->|Tenant-scoped /ask| RuntimeAPI

  ControlPlaneAPI -->|Read/Write Bundles + Aliases| RegistryFS[(Registry: Filesystem)]
  RuntimeAPI -->|Read Bundles (current/candidate/draft)| RegistryFS
  RuntimeAPI -. future cache .-> Redis[(Redis placeholder)]
  ControlPlaneAPI -. observability/auth .-> ExternalServices[(Future Observability / AuthN)]
```

### Interfaces externas
- **Usuário de Plataforma (Admin/Tenant Ops)**: interage com o Control Plane para validar bundles, promover versões e configurar aliases (`draft`, `candidate`, `current`).
- **Cliente Runtime**: chama `/ask` no Runtime com `tenant_id` e alias ou `bundle_id` explícito.

### Dependências e Fronteiras
- **Registry (filesystem)**: origem da verdade para bundles no Stage 0, montado em ambos os serviços.
- **Redis**: definido no `docker-compose.yml` como placeholder; ainda não é consumido pelo código.
- **Outros serviços**: não existem integrações externas obrigatórias no Stage 0; conexões de dados reais são abstraídas e não implementadas (conforme ADR-0005).
