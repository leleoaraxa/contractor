# Runbook — Promoção e rollback de releases (Stage 0)

Objetivo: manter aliases `draft`, `candidate`, `current` alinhados com bundles presentes no registry local (`registry/tenants/<tenant>/bundles`).

## Referências
- Control Plane API:
  - `GET /api/v1/control/tenants/{tenant_id}/aliases`
  - `POST /api/v1/control/tenants/{tenant_id}/aliases/{alias}` (`current|candidate|draft`)
  - `GET /api/v1/control/tenants/{tenant_id}/resolve/{alias}`
- Bundle validation:
  - `GET /api/v1/control/tenants/{tenant_id}/bundles/{bundle_id}/validate`

## Fluxo: candidate → current
1. **Validar bundle candidato**
   ```bash
   curl -s http://localhost:8001/api/v1/control/tenants/demo/bundles/202601050002/validate | jq
   ```
   - Deve retornar `status: "pass"` e `errors: []`.

2. **Promover para `candidate`**
   ```bash
   curl -s -X POST -H "Content-Type: application/json" \
     -d '{"bundle_id":"202601050002"}' \
     http://localhost:8001/api/v1/control/tenants/demo/aliases/candidate | jq
   ```

3. **Promover para `current`**
   ```bash
   curl -s -X POST -H "Content-Type: application/json" \
     -d '{"bundle_id":"202601050002"}' \
     http://localhost:8001/api/v1/control/tenants/demo/aliases/current | jq
   ```

4. **Confirmar resolução**
   ```bash
   curl -s http://localhost:8001/api/v1/control/tenants/demo/resolve/current | jq
   ```

## Rollback para bundle anterior
1. Identifique o bundle anterior (ex.: `202601050001`) e valide se necessário.
2. Reatribua o alias `current`:
   ```bash
   curl -s -X POST -H "Content-Type: application/json" \
     -d '{"bundle_id":"202601050001"}' \
     http://localhost:8001/api/v1/control/tenants/demo/aliases/current | jq
   ```
3. Verifique novamente a resolução de alias e execute um `/ask` para validar comportamento:
   ```bash
   curl -s -X POST -H "Content-Type: application/json" \
     -d '{"tenant_id":"demo","question":"post-rollback check"}' \
     http://localhost:8000/api/v1/runtime/ask | jq
   ```
