# Runbook — Executar testes

## Teste E2E (integração)

O teste `tests/integration/test_e2e_flow.py` valida:

1. **Validação do bundle** via Control Plane (`/bundles/{bundle_id}/validate`).
2. **Promoção** do alias `current` via `/versions/current`.
3. **Execução do runtime /ask** usando o alias `current` (com `PostgresExecutor` mockado).

### Pré-requisitos
- Dependências instaladas (`pip install -e .`).
- Registry local com o bundle demo (`registry/tenants/demo/bundles/202601050001`).

> Observação: o teste usa `FastAPI TestClient` e faz mock de `psycopg2.connect`, portanto não exige um Postgres real. A variável `POSTGRES_DSN` é configurada dentro do próprio teste.

### Comando
```bash
pytest -q tests/integration/test_e2e_flow.py
```
