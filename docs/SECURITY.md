# CONTRACTOR — Segurança e Threat Model (baseline)

## Baseline implementado (ADR 0007, ADR 0013)
- **Autenticação por API key** (`X-API-Key`) para Control Plane e Runtime. Chaves configuradas em `CONTRACTOR_API_KEYS` (lista separada por vírgula).  
- **Toggle de desenvolvimento:** `CONTRACTOR_AUTH_DISABLED=1` desativa a verificação (somente para ambiente local).  
- **Rate limiting token bucket** por tenant (`RATE_LIMIT_RPS`, `RATE_LIMIT_BURST`), preferencialmente via Redis (`RATE_LIMIT_REDIS_URL` ou `RUNTIME_REDIS_URL`) com fallback em memória. Respostas excedidas retornam `429` com `Retry-After`.  
- **Auditoria**: mudanças de alias e execuções de promoção/quality são registradas em `registry/control_plane/audit.log` (JSONL, sem dados sensíveis).  
- **Headers de controle plane no runtime**: chamadas internas carregam o mesmo cabeçalho `X-API-Key` quando o auth está habilitado.

## Threat model mínimo
- **Bypass de autenticação**  
  - *Risco:* acesso não autorizado ao Control Plane ou `/ask`.  
  - *Mitigação:* API key obrigatória por padrão; toggle explícito apenas para dev; redaction de logs.

- **Noisy neighbor / abuso de custo**  
  - *Risco:* tenant gerar carga excessiva, derrubando outros.  
  - *Mitigação:* rate limiting por tenant e escopo (control aliases/quality/validate, runtime `/ask`); resposta `429` padronizada.

- **Alteração silenciosa de release**  
  - *Risco:* troca de alias sem trilha.  
  - *Mitigação:* audit log JSONL com alias anterior/novo e status de promoção/quality.

## Executando com autenticação
1. Defina uma chave em `.env`:
   ```bash
   CONTRACTOR_API_KEYS=dev-key
   CONTRACTOR_AUTH_DISABLED=0
   ```
2. Inclua o header nas chamadas:
   ```bash
   curl -H "X-API-Key: dev-key" http://localhost:8001/api/v1/control/healthz
   curl -H "X-API-Key: dev-key" -X POST -H "Content-Type: application/json" \
     -d '{"tenant_id":"demo","question":"hello"}' \
     http://localhost:8000/api/v1/runtime/ask
   ```

## Executando sem autenticação (apenas dev/local)
```bash
CONTRACTOR_AUTH_DISABLED=1
```
Com o toggle ativo, o header `X-API-Key` torna-se opcional e o rate limiting mantém-se ativo.
