# Evidence — Stage 3 Runtime Resource Isolation (ADR 0022 + ADR 0028)

## Context

Este documento responde ao item **1.2 do checklist do ADR 0028** (“Isolamento de recursos (CPU, memória, cache)”) sob o modelo de **Dedicated Runtime** definido no ADR 0022. O objetivo é registrar evidências concretas no repositório sobre isolamento de CPU, memória e cache por runtime dedicado, ou apontar gaps quando não houver implementação comprovada.

## Evidence Table

| Recurso | Status | Evidência concreta | Gap identificado |
| --- | --- | --- | --- |
| CPU | **PASS** | `docker-compose.yml` define limites de CPU explícitos por runtime dedicado: `runtime` (`cpus: "1.0"`), `worker` (`cpus: "0.5"`) e cache dedicado `redis_runtime` (`cpus: "0.25"`). | Nenhum gap técnico identificado no baseline de Compose; requer aplicação em ambiente real para fechar o item 1.2 do ADR 0028. |
| Memória | **PASS** | `docker-compose.yml` define limites explícitos de memória por runtime dedicado: `runtime` (`mem_limit: "1g"`), `worker` (`mem_limit: "512m"`) e cache dedicado `redis_runtime` (`mem_limit: "256m"`). | Nenhum gap técnico identificado no baseline de Compose; requer aplicação em ambiente real para fechar o item 1.2 do ADR 0028. |
| Cache / Shared State | **PASS** | Cache não é mais compartilhado: `runtime` e `worker` usam `RUNTIME_REDIS_URL=redis://redis_runtime:6379/0` e o Redis dedicado (`redis_runtime`) é isolado do restante dos serviços. | Para múltiplos runtimes dedicados, cada instância deve manter seu Redis dedicado equivalente. |

## OOM Behavior (expected)

Quando o limite de memória é atingido (`mem_limit`), o kernel encerra o container por OOM. Sem uma política explícita de restart no Compose, espera-se que o container do runtime dedicado permaneça parado até intervenção manual (reinício/replace pelo operador). O impacto é isolado ao runtime dedicado afetado.

## Conclusion

**Isolamento de recursos por runtime dedicado = SIM (baseline em Compose).**

**Item 1.2 pronto para fechamento quando aplicado em produção.**
