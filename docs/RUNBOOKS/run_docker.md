# Runbook — Executar com Docker Compose

## Pré-requisitos
- Docker + Docker Compose
- Arquivo `.env` criado a partir de `.env.example`

## Passo a passo
1. **Preparar ambiente**
   ```bash
   cp .env.example .env
   ```

2. **Subir serviços**
   ```bash
   docker compose up --build
   ```
   - Sobe três contêineres: `control`, `runtime`, `redis` (placeholder).
   - Os diretórios do repositório são montados em `/app` nos contêineres.

3. **Verificar healthchecks**
   ```bash
   curl -f http://localhost:8001/api/v1/control/healthz
   curl -f http://localhost:8000/api/v1/runtime/healthz
   ```

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
