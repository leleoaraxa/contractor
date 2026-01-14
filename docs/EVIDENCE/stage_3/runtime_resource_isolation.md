# Evidence — Stage 3 Runtime Resource Isolation (ADR 0022 + ADR 0028)

## Context

Este documento responde ao item **1.2 do checklist do ADR 0028** (“Isolamento de recursos (CPU, memória, cache)”) sob o modelo de **Dedicated Runtime** definido no ADR 0022. O objetivo é registrar evidências concretas no repositório sobre isolamento de CPU, memória e cache por runtime dedicado, ou apontar gaps quando não houver implementação comprovada.

## Evidence Table

| Recurso | Status | Evidência concreta | Gap identificado |
| --- | --- | --- | --- |
| CPU | **FAIL** | `docker-compose.yml` define serviços `control`, `runtime`, `worker` e `redis` sem limites explícitos de CPU (`cpus`, `cpu_quota`, `cpu_shares` ou `deploy.resources`). | Não existe limitação de CPU por runtime dedicado em configuração de infra/versionada. |
| Memória | **FAIL** | `docker-compose.yml` não define limites de memória (`mem_limit` ou `deploy.resources.limits.memory`) para os serviços do runtime/control/worker. O `Dockerfile` também não aplica restrições. | Não há limites de memória por runtime dedicado, nem proteção OOM documentada em infra. |
| Cache / Shared State | **FAIL** | `docker-compose.yml` usa um único serviço `redis` compartilhado, consumido por `runtime` e `worker` via `RUNTIME_REDIS_URL=redis://redis:6379/0`, sem separação por tenant ou runtime dedicado. | Cache é compartilhado entre runtimes (na prática um único Redis), sem isolamento por tenant/runtime dedicado; risco de cache bleed não está mitigado por configuração de infra. |

## Conclusion

**Isolamento de recursos por runtime dedicado = NÃO**

Motivo: não há evidência concreta no repositório de limites explícitos de CPU/memória nem segregação de cache por runtime dedicado, conforme exigido pelo item 1.2 do ADR 0028.
