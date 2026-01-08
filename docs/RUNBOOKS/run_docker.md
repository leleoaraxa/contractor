# Runbook — Executar com Docker Compose

## Pré-requisitos
- Docker + Docker Compose
- Arquivo `.env` criado a partir de `.env.example`
- `POSTGRES_DSN` configurado no `.env` (runtime executa SQL real)

## Passo a passo
1. **Preparar ambiente**
   ```bash
   cp .env.example .env
   ```
  - Para Redis, mantenha `redis://redis:6379/0` (acesso via serviço `redis` do compose).
  - Para usar o Postgres do compose, mantenha `POSTGRES_DSN=postgresql://postgres:contractor@contractor_db:5432/contractor` (default do `.env.example`).
  - Se quiser usar um Postgres externo, ajuste `POSTGRES_DSN` (ex.: `postgresql://user:pass@host.docker.internal:5432/db`).
  - Para async /ask, use `RUNTIME_ASYNC_ENABLED=1` e, se necessário, `RUNTIME_ASYNC_ALWAYS=1` (alias legado `ASYNC_ALWAYS`).
  - Certifique-se de que a rede `contractor_net` exista (`docker network create contractor_net`).

2. **Subir serviços**
   ```bash
   docker compose up --build
   ```
   - Sobe cinco contêineres: `control`, `runtime`, `worker`, `redis`, `contractor_db`.
   - Os diretórios do repositório são montados em `/app` nos contêineres.

3. **Verificar healthchecks**
   ```bash
   curl -f -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" http://localhost:8001/api/v1/control/healthz
   curl -f -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" http://localhost:8000/api/v1/runtime/healthz
   ```
   - Caso `CONTRACTOR_AUTH_DISABLED=1`, o header é opcional.

4. **Smoke test (host)**
   ```bash
   ./scripts/dev/smoke.sh
   ```

5. **Smoke test (dentro do runtime)**
   ```bash
   docker compose exec runtime python -c "import urllib.request; print(urllib.request.urlopen('http://control:8001/api/v1/control/healthz').read().decode())"
   ```

6. **Async /ask (worker + polling)**
   ```bash
   curl -s -X POST -H "Content-Type: application/json" \
     -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
     -H "X-Async: 1" \
     -d '{"tenant_id":"demo","question":"health status","release_alias":"current"}' \
     http://localhost:8000/api/v1/runtime/ask | jq
   ```

   Em seguida, use o `request_id` para polling:
   ```bash
   curl -s -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
     http://localhost:8000/api/v1/runtime/ask/result/<request_id> | jq
   ```

## Encerrar
```bash
docker compose down
```
