# Runbook — Executar localmente (sem Docker)

## Pré-requisitos
- Python 3.11+
- `pip install -e .` na raiz do repositório (usa `pyproject.toml`)
- Arquivo `.env` criado a partir de `.env.example`

## Passo a passo
1. **Preparar ambiente**
   ```bash
   cp .env.example .env
   pip install -e .
   ```

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

## Parâmetros importantes (.env)
- `CONTROL_BASE_URL` deve apontar para o host/porta do Control Plane acessível pelo Runtime (default: `http://localhost:8001`).
- `BUNDLE_REGISTRY_BASE` deve permanecer como `registry/tenants` no Stage 0 (filesystem).

## Estrutura esperada
- `registry/tenants/demo/bundles/*` com manifests de exemplo.
- `registry/control_plane/tenant_aliases.json` com aliases iniciais (`current` já apontando para `202601050001`).
