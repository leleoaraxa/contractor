# Runbook — Runtime /ask pipeline (PostgresExecutor)

Este runbook descreve o pipeline atual do runtime, incluindo resolução de alias e execução SQL real via `PostgresExecutor`.

## Endpoints do runtime

- `POST /api/v1/runtime/ask`
- `GET /api/v1/runtime/ask/result/{request_id}`
- `GET /api/v1/runtime/healthz`

## Como validar runtime healthz

```bash
curl -f -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
  http://localhost:8000/api/v1/runtime/healthz
```

> Com `CONTRACTOR_AUTH_DISABLED=1`, o header `X-API-Key` é opcional.

## Como rodar smoke.sh

Ao executar `scripts/dev/smoke.sh` dentro do container, certifique-se de que a imagem tenha `curl` instalado.

## Pipeline /ask (resumo)

1. **Autenticação e rate limit**
   - O rate limiter usa Redis quando configurado; se a lib `redis` estiver ausente ou o Redis estiver indisponível, o runtime responde com `rate_limit_backend_unavailable` (sem fallback silencioso).
   - Se **nenhum** Redis estiver configurado, o runtime usa o backend in-memory com warning explícito (apenas para uso local).
2. **Resolução de bundle_id**
   - Se `bundle_id` não for informado, o runtime resolve via Control Plane:
     `GET /api/v1/control/tenants/{tenant_id}/versions/{alias}/resolve`
3. **Carga do manifest**
   - `ArtifactLoader` lê o registry local (`BUNDLE_REGISTRY_BASE`).
4. **Planner + Builder**
   - Decisão de intent/entity com `Planner` + `OntologyLoader` (quando disponível).
   - Para o bundle demo, apenas termos fortes como `health`/`status` roteiam para `health_check`.
   - Saudações como `hello contractor` retornam `intent/entity=null` com `reason=no_match`.
5. **Execução SQL real**
   - Apenas quando o `plan.action` exige SQL e existe `entity_id`.
   - Caso contrário, o runtime retorna `execution.status=skipped` (sem 500).
   - `PostgresExecutor` usa `POSTGRES_DSN` e executa `SELECT * FROM <entity> LIMIT 10`.
6. **Decisão sync vs async (cache miss)**
   - Se cache hit, responde `200` imediatamente.
   - Se cache miss e `X-Async: 1` (ou `RUNTIME_ASYNC_ALWAYS=1`, alias legado `ASYNC_ALWAYS`), o runtime enfileira o job no Redis e retorna `202` com `request_id`.
   - Se Redis estiver indisponível, o runtime retorna `503` com `detail.error=async_unavailable`.
7. **Execução + formatação + cache**
   - `Formatter` monta resposta e `RuntimeCache` guarda resultado (quando habilitado).

## Async polling (worker + result store)

Quando o `/ask` retorna `202`, o cliente deve consultar o resultado usando:

```bash
curl -s -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
  http://localhost:8000/api/v1/runtime/ask/result/<request_id> | jq
```

Estados possíveis:
- `404` com `{detail:{error:"not_ready"}}` enquanto o worker não processou.
- `404` com `{detail:{error:"expired"}}` quando a chave expira.
- `200` com o mesmo payload do `/ask` síncrono quando pronto.

TTL do resultado é controlado por `RUNTIME_ASYNC_RESULT_TTL_SECONDS` (default: 600).

## Exemplo de request

```bash
curl -s -X POST -H "Content-Type: application/json" \
  -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
  -d '{"tenant_id":"demo","question":"health status","release_alias":"current"}' \
  http://localhost:8000/api/v1/runtime/ask | jq
```

> O campo `release_alias` aceita `draft|candidate|current`. Se `bundle_id` for informado no payload, o runtime ignora `release_alias`.

## Configuração (env vars relevantes)

Baseado em `.env.example` e `app/shared/config/settings.py`:

### Runtime
- `RUNTIME_HOST`, `RUNTIME_PORT`, `RUNTIME_BASE_URL`
- `RUNTIME_REDIS_URL` (cache e fila async)
- `POSTGRES_DSN` (**obrigatório** para `PostgresExecutor`)
- Dependência Python: `redis` (necessário para o rate limiter usar Redis)
- Async: `RUNTIME_ASYNC_ALWAYS` (alias legado `ASYNC_ALWAYS`), `RUNTIME_ASYNC_ENABLED`, `RUNTIME_ASYNC_QUESTION_LENGTH_THRESHOLD`, `RUNTIME_ASYNC_RESULT_TTL_SECONDS`, `RUNTIME_ASYNC_WORKER_BLOCK_SECONDS`

### Control Plane (necessário para resolução de alias)
- `CONTROL_BASE_URL`
- `CONTROL_HOST`, `CONTROL_PORT`

### Registro de bundles
- `BUNDLE_REGISTRY_BASE`

### Segurança e limites
- `CONTRACTOR_API_KEYS` / `CONTRACTOR_API_KEY`
- `CONTRACTOR_AUTH_DISABLED`
- `RATE_LIMIT_RPS`, `RATE_LIMIT_BURST`, `RATE_LIMIT_REDIS_URL`

## Como o runtime obtém artefatos

O runtime resolve o bundle através do `ControlPlaneClient` e, em seguida, carrega o manifest via `ArtifactLoader` no filesystem local. Isso mantém o runtime sem estado, mas dependente do Control Plane para a seleção do bundle.
