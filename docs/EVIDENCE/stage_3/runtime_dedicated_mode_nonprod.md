# Evidence — Dedicated Runtime Mode (Non-Prod/Local/Compose)

## Escopo (importante)

Este documento **não** é evidência de produção. Ele cobre **apenas** o modo dedicado em **non-prod/local/compose**, conforme ADR 0022 / ADR 0028 (itens 1.1 e 1.3). Não há promessa de produção aqui.

## Pré-requisitos

- `RUNTIME_DEDICATED_TENANT_ID` definido para o tenant dedicado.
- `CONTRACTOR_API_KEYS` definido para autenticação do runtime.
- Ambiente local com Docker Compose.

> Sugestão: use `.env` com valores locais. Por exemplo:
>
> ```bash
> cp .env.example .env
> printf '\nRUNTIME_DEDICATED_TENANT_ID=tenant-alpha\nCONTRACTOR_API_KEYS=local-test-key\n' >> .env
> ```

## Passo a passo (executável)

1. Suba o stack local (compose):

```bash
docker compose up -d control runtime worker redis_runtime contractor_db
```

2. Faça uma request com tenant **diferente** do dedicado (espera **403**):

```bash
curl -s -o /tmp/runtime_mismatch.json -w "%{http_code}\n" \
  -X POST http://localhost:8000/api/v1/runtime/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: local-test-key" \
  -d '{"tenant_id":"tenant-beta","question":"ping"}'
```

3. Faça uma request com tenant **igual** ao dedicado (espera **200**):

```bash
curl -s -o /tmp/runtime_match.json -w "%{http_code}\n" \
  -X POST http://localhost:8000/api/v1/runtime/ask \
  -H "Content-Type: application/json" \
  -H "X-API-Key: local-test-key" \
  -d '{"tenant_id":"tenant-alpha","question":"ping"}'
```

## Resultado esperado (non-prod)

- **Request com tenant diferente**:
  - HTTP **403**.
  - Corpo (trecho de erro estruturado):

```json
{
  "detail": {
    "error": "dedicated_tenant_mismatch"
  }
}
```

- **Request com tenant igual**:
  - HTTP **200**.
  - Corpo contendo resposta do runtime (exemplo simplificado):

```json
{
  "answer": "..."
}
```

## Observações

- Evidência limitada ao ambiente local/compose. Produção exige execução dedicada real e validação operacional.
- Complemento técnico: `tests/integration/test_dedicated_runtime_mode.py` valida o mesmo comportamento em integração local.
