# Stage 3 / ADR 0028 / Audit logs — Evidência (non-prod)

**Escopo:** evidência operacional em ambiente compose/local (não produção).

**Referências:** ADR 0028; `docs/RUNBOOKS/release_promotion.md`; `docs/RUNBOOKS/privacy_retention.md`; `tests/integration/test_control_plane_audit_log.py`.

## Commands executed (compose/local)

```bash
docker compose up -d control

curl -sS -X PUT \
  "http://localhost:8001/api/v1/control/tenants/demo/versions/draft" \
  -H "X-API-Key: dev-key" \
  -H "Content-Type: application/json" \
  -d '{"bundle_id":"202601050001"}'

tail -n 1 registry/control_plane/audit.log
```

## Observed output

```json
{"ts":"2025-01-20T12:00:00+00:00","action":"alias.set","tenant_id":"demo","actor":"key_hash:…","target":{"alias":"draft","bundle_id":"202601050001"},"previous_bundle_id":null}
```

## Automated test

```bash
pytest -q tests/integration/test_control_plane_audit_log.py
```

## What this proves

- Uma ação sensível do control plane (set de alias) gera evento auditável em JSONL.
- O evento contém `tenant_id`, `actor`, `action`, `target` e `ts`.
- O log é escrito no caminho configurado por `CONTROL_AUDIT_LOG_PATH`.

## What this does NOT prove

- NÃO é produção.
- NÃO fecha qualquer requisito de auditoria em produção sem tenant enterprise ativo.
- NÃO valida integração com SIEM/ELK (Stage 4).
