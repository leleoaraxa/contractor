# Runbook — Promoção e rollback de releases (Stage 0)

Objetivo: manter aliases `draft`, `candidate`, `current` alinhados com bundles presentes no registry local (`registry/tenants/<tenant>/bundles`).

## Ciclo de vida dos aliases

```
draft -> candidate -> current
```

- `draft`: permite validar o bundle sem rodar suites de qualidade.
- `candidate`: exige validação + suites definidas no promotion set do tenant.
- `current`: exige validação + suites definidas no promotion set do tenant.

## Endpoints reais (Control Plane)

### Alias store usado pelo runtime (`versions.py`)
- `GET /api/v1/control/tenants/{tenant_id}/versions`
- `PUT /api/v1/control/tenants/{tenant_id}/versions/{alias}` (`draft|candidate|current`)
- `GET /api/v1/control/tenants/{tenant_id}/versions/{alias}/resolve`

### Alias store com gate de qualidade (`tenants.py`)
- `GET /api/v1/control/tenants/{tenant_id}/aliases`
- `POST /api/v1/control/tenants/{tenant_id}/aliases/{alias}` (`draft|candidate|current`)
- `GET /api/v1/control/tenants/{tenant_id}/resolve/{alias}`

### Bundle validation (`bundles.py`)
- `GET /api/v1/control/tenants/{tenant_id}/bundles/{bundle_id}/validate`

> Observação: os endpoints de `aliases` executam o gate de qualidade (validation + suites). Os endpoints de `versions` são o mapeamento simples de alias que o runtime resolve via `ControlPlaneClient`.

## Fluxo: candidate → current (via endpoints de versões)

1. **Validar o bundle candidato**
   ```bash
   curl -s -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
     http://localhost:8001/api/v1/control/tenants/demo/bundles/202601050002/validate | jq
   ```

2. **Promover para `candidate`**
   ```bash
   curl -s -X PUT -H "Content-Type: application/json" \
     -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
     -d '{"bundle_id":"202601050002"}' \
     http://localhost:8001/api/v1/control/tenants/demo/versions/candidate | jq
   ```

3. **Promover para `current`**
   ```bash
   curl -s -X PUT -H "Content-Type: application/json" \
     -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
     -d '{"bundle_id":"202601050002"}' \
     http://localhost:8001/api/v1/control/tenants/demo/versions/current | jq
   ```

4. **Confirmar resolução**
   ```bash
   curl -s http://localhost:8001/api/v1/control/tenants/demo/versions/current/resolve | jq
   ```

## Promoção com gate de qualidade (recomendado)

Para exigir validation + suites antes de alterar `candidate`/`current`, use os endpoints de `aliases`:

```bash
curl -s -X POST -H "Content-Type: application/json" \
  -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
  -d '{"bundle_id":"202601050002"}' \
  http://localhost:8001/api/v1/control/tenants/demo/aliases/candidate | jq

curl -s -X POST -H "Content-Type: application/json" \
  -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
  -d '{"bundle_id":"202601050002"}' \
  http://localhost:8001/api/v1/control/tenants/demo/aliases/current | jq
```

## Rollback para bundle anterior

1. Identifique o bundle anterior (ex.: `202601050001`) e valide se necessário.
2. Reatribua o alias `current` (via `aliases` ou `versions`).

```bash
curl -s -X POST -H "Content-Type: application/json" \
  -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
  -d '{"bundle_id":"202601050001"}' \
  http://localhost:8001/api/v1/control/tenants/demo/aliases/current | jq
```

3. Verifique novamente a resolução de alias e execute um `/ask` para validar comportamento:
   ```bash
   curl -s -X POST -H "Content-Type: application/json" \
     -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
     -d '{"tenant_id":"demo","question":"post-rollback check"}' \
     http://localhost:8000/api/v1/runtime/ask | jq
   ```

## Script auxiliar

- `scripts/release/promote_candidate_to_current.ps1`

> Dica: com `CONTRACTOR_AUTH_DISABLED=1`, o header `X-API-Key` é opcional. Toda promoção/alteração de alias gera uma linha em `registry/control_plane/audit.log`.
