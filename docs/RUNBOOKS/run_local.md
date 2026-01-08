# Runbook — Executar localmente (sem Docker)

## Pré-requisitos
- Python 3.11+
- `pip install -e .` na raiz do repositório (usa `pyproject.toml`)
- Arquivo `.env` criado a partir de `.env.example`
- `POSTGRES_DSN` configurado no `.env` (runtime executa SQL real)

## Passo a passo
1. **Preparar ambiente**
   ```bash
   cp .env.example .env
   pip install -e .
   ```
   - Adicione `POSTGRES_DSN` no `.env` (ex.: `postgresql://user:pass@localhost:5432/db`).

2. **Subir Control Plane**
   ```bash
   ./scripts/dev/run_control.sh
   ```

3. **Subir Runtime**
   Em outro terminal:
   ```bash
   ./scripts/dev/run_runtime.sh
   ```

4. **Fazer smoke local**
   Com ambos serviços rodando:
   ```bash
   ./scripts/dev/smoke.sh
   ```
   - Se `CONTRACTOR_AUTH_DISABLED=0`, defina uma chave em `.env` (`CONTRACTOR_API_KEYS=dev-key`) e passe `X-API-Key` nas chamadas (o script já lê `CONTRACTOR_API_KEYS` automaticamente).

## Parâmetros importantes (.env)
- `CONTROL_BASE_URL` deve apontar para o host/porta do Control Plane acessível pelo Runtime (default: `http://localhost:8001`).
- `BUNDLE_REGISTRY_BASE` deve permanecer como `registry/tenants` no Stage 0 (filesystem).
- `CONTRACTOR_API_KEYS` define a lista de chaves aceitas; `CONTRACTOR_AUTH_DISABLED=1` libera chamadas locais sem header.
- `RATE_LIMIT_RPS` e `RATE_LIMIT_BURST` controlam o token bucket por tenant; `RATE_LIMIT_REDIS_URL`/`RUNTIME_REDIS_URL` habilitam backend Redis (se o Redis configurado estiver indisponível, o runtime retorna `rate_limit_backend_unavailable` e não faz fallback silencioso).

## Estrutura esperada
- `registry/tenants/demo/bundles/*` com manifests de exemplo.
- `registry/control_plane/tenant_aliases.json` com aliases iniciais (`current` já apontando para `202601050001`).
