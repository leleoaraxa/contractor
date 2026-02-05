# ADR 0013 — Rate limiting e quotas (policy-driven)

**Status:** Accepted  
**Data:** 2026-02-05  
**Decide:** Política v1 de limitação de taxa e quotas por tenant no Runtime  
**Relacionados:** ADR 0004, ADR 0006, ADR 0007, ADR 0012

---

## Contexto

Os ADRs 0004 e 0007 exigem comportamento determinístico, auditável e tenant-aware, incluindo negação por política. O Runtime já aplica autenticação v1 (ADR 0012), mas não havia contrato explícito para rate limiting e quotas por tenant.

Precisamos de um contrato mínimo, verificável e fail-closed, sem heurísticas e sem acoplamento a storage distribuído nesta versão.

---

## Decisão

### 1) Escopo v1

- Enforcement **apenas no Runtime**.
- Aplicação **apenas no endpoint `POST /execute`**.
- Modelo de contagem em memória, process-local, por janela fixa (fixed window).

### 2) Fonte da policy (precedência)

O Runtime carrega a policy na seguinte ordem:

1. `CONTRACTOR_RATE_LIMIT_POLICY_JSON` (JSON em env, precedência máxima)
2. `CONTRACTOR_RATE_LIMIT_POLICY_PATH` (path para arquivo YAML/JSON)
3. default versionado: `data/runtime/rate_limit_policy.yaml`

Se a policy estiver ausente, inválida, não parseável ou com schema inválido, o comportamento é **fail-closed** com **HTTP 500**.

### 3) Formato da policy (v1)

YAML/JSON equivalente:

```yaml
rate_limit:
  window_seconds: 60
  max_requests: 30
quota:
  window_seconds: 86400
  max_requests: 2000
tenants:
  "*":
    rate_limit:
      window_seconds: 60
      max_requests: 60
    quota:
      window_seconds: 86400
      max_requests: 5000
  "tenant_a":
    rate_limit:
      window_seconds: 60
      max_requests: 10
    quota:
      window_seconds: 86400
      max_requests: 100
```

Regras obrigatórias:

- `tenants` deve existir e ser dict não-vazio.
- `"*"` é obrigatório como baseline.
- `rate_limit` e `quota` globais são obrigatórios.
- Para cada bucket (`rate_limit`/`quota`), `window_seconds` e `max_requests` devem ser `int > 0`.
- Não existe auto-cálculo de limites.

### 4) Contrato de erro

- Policy ausente/inválida: **500**.
- Rate limit excedido: **429 Too Many Requests**, `detail="Rate limit exceeded"`.
- Quota excedida: **429 Too Many Requests**, `detail="Quota exceeded"`.
- Em 429, header obrigatório: `Retry-After: <segundos_int>`.
- 401/403 da autenticação permanecem inalterados e ocorrem antes do enforcement.

### 5) Transparência mínima no Runtime

Em respostas de `POST /execute`:

- Em **200** e **429**:
  - `X-RateLimit-Limit`
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`
- Em **429**:
  - `Retry-After`

`X-RateLimit-*` representa o bucket de `rate_limit` (não quota), para manter contrato simples e determinístico em v1.

### 6) Algoritmo v1 (determinístico)

- `now = int(time.time())`
- `window_start = now - (now % window_seconds)`
- chave do contador: `(tenant_id, bucket_name, window_start)`
- buckets: `rate_limit` e `quota`
- ao exceder:
  - `429`
  - `Retry-After = (window_start + window_seconds) - now` (mínimo 1)

---

## Consequências

### Positivas

- Contrato explícito, policy-driven e auditável.
- Sem hardcode de domínio para limites/quotas.
- Fail-closed consistente com ADRs existentes.

### Limitações conhecidas (aceitas em v1)

- Contadores em memória por processo (sem coordenação distribuída).
- Reinício do processo zera contadores.
- Sem Redis/storage distribuído nesta fase.

Essas limitações serão evoluídas em ADRs posteriores quando necessário.

---

## Fora de escopo

- Redis, locks distribuídos, sliding window avançada.
- Billing e planos comerciais.
- Novos endpoints.
- Mudanças no contrato de authn/authz existente.
- Pipeline de auditoria completa (ADR 0014).

---

## Implementação vinculada

- Runtime: enforcement policy-driven em `POST /execute` com fail-closed para policy inválida/ausente.
- Policy default versionada em `data/runtime/rate_limit_policy.yaml`.
- Testes determinísticos com monkeypatch de `time.time()` cobrindo 200/429/500.
