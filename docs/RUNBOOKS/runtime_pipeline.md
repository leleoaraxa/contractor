# Runbook — Runtime /ask pipeline (PostgresExecutor)

Este runbook descreve o pipeline atual do runtime, incluindo resolução de alias e execução SQL real via `PostgresExecutor`.

## Endpoints do runtime

- `POST /api/v1/runtime/ask`
- `GET /api/v1/runtime/healthz`

## Como validar runtime healthz

```bash
curl -f -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
  http://localhost:8000/api/v1/runtime/healthz
```

> Com `CONTRACTOR_AUTH_DISABLED=1`, o header `X-API-Key` é opcional.

## Pipeline /ask (resumo)

1. **Autenticação e rate limit**
   - Se o Redis estiver indisponível, o runtime pode cair para a política in-memory. Isso não invalida o smoke, mas pode alterar o comportamento conforme os thresholds configurados.
2. **Resolução de bundle_id**
   - Se `bundle_id` não for informado, o runtime resolve via Control Plane:
     `GET /api/v1/control/tenants/{tenant_id}/versions/{alias}/resolve`
3. **Carga do manifest**
   - `ArtifactLoader` lê o registry local (`BUNDLE_REGISTRY_BASE`).
4. **Planner + Builder**
   - Decisão de intent/entity com `Planner` + `OntologyLoader` (quando disponível).
5. **Execução SQL real**
   - Apenas quando o `plan.action` exige SQL e existe `entity_id`.
   - Caso contrário, o runtime retorna `execution.status=skipped` (sem 500).
   - `PostgresExecutor` usa `POSTGRES_DSN` e executa `SELECT * FROM <entity> LIMIT 10`.
6. **Formatação + cache**
   - `Formatter` monta resposta e `RuntimeCache` guarda resultado (quando habilitado).

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
- `RUNTIME_REDIS_URL` (cache opcional)
- `POSTGRES_DSN` (**obrigatório** para `PostgresExecutor`)

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
