# Runbook — Troubleshooting (Stage 0)

Problemas comuns ao subir o Control Plane + Runtime localmente.

## Alias não resolvido (`alias not set`)
- **Sintoma**: `/versions/{alias}/resolve` retorna 404 ou `/ask` retorna `bundle_id not provided and alias not set`.
- **Ação**:
  1. Verificar aliases atuais (store usado pelo runtime):
     ```bash
     curl -s -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
       http://localhost:8001/api/v1/control/tenants/demo/aliases | jq
     ```
  2. Reatribuir `current` para o bundle conhecido (gate obrigatório para `candidate/current`):
     ```bash
     curl -s -X POST -H "Content-Type: application/json" \
       -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
       -d '{"bundle_id":"202601050001"}' \
       http://localhost:8001/api/v1/control/tenants/demo/aliases/current | jq
     ```
  3. O endpoint `/versions` resolve é público e usado pelo runtime:
     ```bash
     curl -s http://localhost:8001/api/v1/control/tenants/demo/versions/current/resolve | jq
     ```

## smoke_quality_gate: Runtime health check failed
- **Sintoma**: `Runtime health check failed` ao rodar `scripts/quality/smoke_quality_gate.py`.
- **Ação**:
  1. Verifique se o runtime está ativo:
     ```bash
     curl -f -H "X-API-Key: ${CONTRACTOR_API_KEYS%%,*}" \
       http://localhost:8000/api/v1/runtime/healthz
     ```
  2. Se estiver rodando via docker-compose, confirme que a porta 8000 está exposta e que o serviço `runtime` está healthy.
  3. Se você passou `--runtime-base` com `/api/v1/runtime`, use apenas a raiz (ex.: `http://localhost:8000`).

## Manifest ou diretório ausente
- **Sintoma**: validação falha com `manifest not found` ou `bundle.missing_dir`.
- **Ação**:
  1. Confirme a estrutura em `registry/tenants/<tenant>/bundles/<bundle_id>/`.
  2. Rode a validação explicitamente:
     ```bash
     curl -s http://localhost:8001/api/v1/control/tenants/demo/bundles/202601050001/validate | jq
     ```
  3. Recrie diretórios faltantes ou corrija `paths` no `manifest.yaml`.

## Control Plane inacessível pelo Runtime
- **Sintoma**: `/ask` retorna erro contendo `control_plane.url` e `status` não 200.
- **Ação**:
  1. Verifique `CONTROL_BASE_URL` no `.env` (deve ser acessível do Runtime).
  2. Em Docker, use `http://control:8001` (já padrão no `docker-compose.yml`).
  3. Teste reachability:
     ```bash
     curl -f http://localhost:8001/api/v1/control/healthz
     docker compose exec runtime python -c "import urllib.request; print(urllib.request.urlopen('http://control:8001/api/v1/control/healthz').read())"
     ```

## Runtime falha ao iniciar (POSTGRES_DSN ausente)
- **Sintoma**: erro `POSTGRES_DSN environment variable is not set.` ao subir o runtime.
- **Ação**:
  1. Defina `POSTGRES_DSN` no `.env` (ex.: `postgresql://user:pass@localhost:5432/db`).
  2. Reinicie o runtime.

## smoke rate limit retorna 500
- **Sintoma**: `scripts/dev/smoke.ps1` ou `scripts/dev/smoke.sh` falha no bloco “Rate limit enforcement” com `500 Internal Server Error`.
- **Causa provável**: o runtime tentou executar SQL sem `entity_id` no plano (`plan.entity_id` ausente).
- **Ação**:
  1. Confirme que o runtime está na versão com guardrail que marca execução como `skipped` quando não há entidade.
  2. Reexecute o smoke e inspecione o corpo retornado (os scripts agora imprimem o body e, se necessário, o `X-Explain: 1`).

## quality/run falha com HTTP 500 calling runtime
- **Sintoma**: `quality/run` falha com `HTTP 500 calling http://runtime:8000/api/v1/runtime/ask`.
- **Causa provável**: plano inválido sem `entity_id`, causando falha na execução SQL.
- **Ação**:
  1. Atualize o runtime para ignorar execução SQL em planos `noop`/sem entidade.
  2. Rode novamente o endpoint `POST /api/v1/control/.../quality/run` e valide que o `execution.status` está `skipped`.
