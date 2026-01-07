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
   - Adicione `POSTGRES_DSN` no `.env` (ex.: `postgresql://user:pass@host.docker.internal:5432/db`).

2. **Subir serviços**
   ```bash
   docker compose up --build
   ```
   - Sobe três contêineres: `control`, `runtime`, `redis` (placeholder).
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

## Encerrar
```bash
docker compose down
```
