# Stage 3 / ADR 0028 / Rotação e revogação de credenciais — Evidência (non-prod)

**Escopo:** evidência operacional **non-prod** em ambiente compose/local. **Sem produção.**

**Referências:**
- ADR 0027 — Enterprise Access Control and Identity Boundaries
- ADR 0028 — Stage 3 Completion and Readiness Checklist
- Runbooks: `docs/RUNBOOKS/stage_3_enterprise/suspected_breach.md`, `docs/RUNBOOKS/release_promotion.md`

## Nota sobre código

Nenhuma alteração de código foi necessária. O modelo atual já valida `X-API-Key` com base em `CONTRACTOR_API_KEYS`, permitindo revogação/rotação via atualização de configuração e restart controlado no ambiente local/compose.

## Procedimento operacional mínimo (non-prod)

1. **Revogação de API key comprometida**
   - Remover a chave comprometida do `CONTRACTOR_API_KEYS` (arquivo `.env` usado pelo compose).
   - Reiniciar `control` e `runtime` para recarregar a configuração.
2. **Geração/ativação de nova key**
   - Criar nova chave (ex.: nova entrada com escopo `tenant-alpha:tenant_runtime_client:<new-key>`).
   - Inserir a nova chave em `CONTRACTOR_API_KEYS` e reiniciar serviços.
3. **Impacto esperado em requests**
   - Requests com a chave revogada passam a retornar **403 (invalid API key)**.
   - Requests com a nova chave passam a retornar **200 OK**.

## Evidência operacional (compose/local)

```bash
# 1) Ambiente local/compose (control + runtime)
docker compose up -d control runtime

# 2) Request com chave antiga (antes da revogação) → 200
curl -s -o /dev/null -w '%{http_code}\n' \
  -X POST http://localhost:8000/api/v1/runtime/ask \
  -H "X-API-Key: old-key-redacted" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"tenant-alpha","question":"ping","bundle_id":"b1"}'

# 3) Rotação: atualizar CONTRACTOR_API_KEYS (remover old-key, adicionar new-key)
# (redigido; arquivo .env local)
cat > .env <<'ENV'
CONTRACTOR_API_KEYS=tenant-alpha:tenant_runtime_client:new-key-redacted
ENV

# 4) Reiniciar serviços para recarregar as chaves
docker compose up -d --force-recreate control runtime

# 5) Request com chave antiga (revogada) → 403
curl -s -o /dev/null -w '%{http_code}\n' \
  -X POST http://localhost:8000/api/v1/runtime/ask \
  -H "X-API-Key: old-key-redacted" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"tenant-alpha","question":"ping","bundle_id":"b1"}'

# 6) Request com chave nova → 200
curl -s -o /dev/null -w '%{http_code}\n' \
  -X POST http://localhost:8000/api/v1/runtime/ask \
  -H "X-API-Key: new-key-redacted" \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"tenant-alpha","question":"ping","bundle_id":"b1"}'
```

**Observed output (redacted):**

```
200
403
200
```

## What this proves

- É possível **revogar** uma API key via atualização de `CONTRACTOR_API_KEYS` e restart local/compose.
- Requests subsequentes com a chave revogada retornam **403**.
- Uma nova chave ativada passa a autorizar o mesmo fluxo com **200 OK**.

## What this does NOT prove

- **Não é produção** e não encerra requisitos de produção do ADR 0028.
- **Não prova automação enterprise** de rotação/revogação (sem IAM externo, sem orquestração).
- **Não comprova integração com SIEM/KMS** (Stage 4), que permanece fora de escopo.
