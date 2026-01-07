# CONTRACTOR Docs

## Quickstart (local)

```bash
cp .env.example .env
# defina POSTGRES_DSN no .env
pip install -e .
./scripts/dev/run_all.sh
```

## Quickstart (Docker Compose)

```bash
cp .env.example .env
# defina POSTGRES_DSN no .env
docker compose up --build
```

## Runbooks

- `docs/RUNBOOKS/run_local.md`
- `docs/RUNBOOKS/run_docker.md`
- `docs/RUNBOOKS/release_promotion.md`
- `docs/RUNBOOKS/runtime_pipeline.md`
- `docs/RUNBOOKS/run_tests.md`
- `docs/RUNBOOKS/troubleshooting.md`

## ADRs e arquitetura

- `docs/ADR/` (decisões arquiteturais)
- `docs/C4/` (diagramas)
- `docs/FOUNDATION.md`
- `docs/SECURITY.md`

## Relatórios gerados

Relatórios em `contractor/out/` são gerados por pipelines locais. Eles foram arquivados em:

```
docs/backup/data/contractor/out/
```
