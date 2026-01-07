# Quality Gate Report (Control Plane)

## Endpoints
* `GET /api/v1/control/tenants/{tenant_id}/bundles/{bundle_id}/quality` — retorna o último relatório persistido para o bundle. 404 se não existir.
* `POST /api/v1/control/tenants/{tenant_id}/bundles/{bundle_id}/quality/run` — executa `validate_bundle` + suites do promotion set do tenant e persiste o relatório.

### Payloads e campos relevantes
* O relatório inclui:
  * `validate`: saída de `validate_bundle` (status + errors).
  * `required_suites`: lista de suites carregadas de `registry/control_plane/promotion_sets/{tenant_id}.yaml` (fallback: `demo_routing_candidate_suite` + `demo_thresholds_suite`).
  * `suites`: resultados detalhados de cada suite (`status`, `passed/total`, `failures`, timestamps, `suite_source`).
  * `result`: `status` (`pass`|`fail`) e `failures` agregados.
  * `timestamps`: `started_at` e `finished_at` (UTC ISO).
  * `commit_hash`: hash do commit git (quando disponível).

## Storage (file-backed)
* Relatórios: `registry/control_plane/quality_reports/{tenant_id}/{bundle_id}.json`.
* Promotion sets por tenant: `registry/control_plane/promotion_sets/{tenant_id}.yaml` (campo raiz `suites: [...]`). Exemplo incluído para `demo`.

## Fluxo candidate → current (com rollback)
1. **Preparar bundle**: subir para registry (`registry/tenants/{tenant}/bundles/{bundle_id}`) e garantir `manifest.yaml` válido.
2. **Qualidade**: chamar `POST /quality/run` apontando para o `bundle_id`. Isso roda validação + suites do promotion set e grava o relatório.
3. **Promover para candidate**: `POST /tenants/{tenant_id}/aliases/candidate { bundle_id }` (ou rota genérica `/aliases/{release_alias}`) — exige `validate`=pass e suites obrigatórias passadas.
4. **Promover para current**: `POST /tenants/{tenant_id}/aliases/current { bundle_id }` — também exige gates aprovados.
5. **Rollback**: reverter com o mesmo endpoint de alias apontando para o `bundle_id` anterior (o script `scripts/release/promote_candidate_to_current.ps1` imprime o comando de rollback após a promoção). O smoke `scripts/quality/smoke_quality_gate.py` promove e já faz rollback automático no final.

## Ferramentas auxiliares
* Runner reutilizável: `app/control_plane/domain/quality/runner.py` (usado pelo CLI `scripts/quality/run_routing_suite.py`).
* Script de promoção atualizado: `scripts/release/promote_candidate_to_current.ps1` chama `/quality/run` e mostra resumo do relatório antes do `set current`.
* Smoke test: `scripts/quality/smoke_quality_gate.py` roda o fluxo (quality → candidate → current → rollback).

