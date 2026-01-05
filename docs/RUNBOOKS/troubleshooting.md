# Runbook — Troubleshooting (Stage 0)

Problemas comuns ao subir o Control Plane + Runtime localmente.

## Alias não resolvido (`alias not set`)
- **Sintoma**: `/resolve/{alias}` retorna 404 ou `/ask` retorna `bundle_id not provided and alias not set`.
- **Ação**:
  1. Verificar aliases atuais:
     ```bash
     curl -s http://localhost:8001/api/v1/control/tenants/demo/aliases | jq
     ```
  2. Reatribuir `current` para o bundle conhecido:
     ```bash
     curl -s -X POST -H "Content-Type: application/json" \
       -d '{"bundle_id":"202601050001"}' \
       http://localhost:8001/api/v1/control/tenants/demo/aliases/current | jq
     ```

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
