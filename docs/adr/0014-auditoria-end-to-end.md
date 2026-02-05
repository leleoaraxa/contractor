# ADR 0014 — Auditoria end-to-end (formato, correlação e retenção mínima)

**Status:** Draft  
**Data:** 2026-02-XX  
**Decide:** Contrato mínimo auditável para eventos de auditoria no Runtime e no Control Plane.  
**Relacionados:** ADR 0004, ADR 0006, ADR 0007, ADR 0010, ADR 0011, ADR 0012, ADR 0013

---

## Contexto

O ADR 0004 define auditoria mínima obrigatória, mas não fixa contrato de evento, correlação entre serviços,
redaction e retenção mínima. Com a integração Runtime ↔ Control Plane (ADR 0010), é necessário um modelo
end-to-end determinístico, sem heurística e com fail-closed quando auditoria obrigatória estiver habilitada.

---

## Decisão (v1 mínima)

### 1) Esquema mínimo do evento (JSONL)

Cada request gera **exatamente 1 evento por serviço**.

Campos obrigatórios:
- `ts_utc` (ISO-8601 UTC, ex.: `2026-02-05T13:45:12Z`)
- `service` (`runtime` | `control_plane`)
- `event` (`execute` | `resolve_current`)
- `tenant_id` (string)
- `request_id` (string, correlação end-to-end)
- `actor` (`external_client` no Runtime, `runtime` no Control Plane)
- `outcome` (`ok` | `error`)
- `http_status` (int)
- `latency_ms` (int)

Campos opcionais:
- `bundle_id` (quando resolvido)
- `control_plane_status` (no Runtime, quando houver chamada ao CP)
- `rate_limit` com `limit`, `remaining`, `reset` (no Runtime quando aplicável)
- `error_code` (`unauthorized`, `forbidden`, `rate_limit_exceeded`, `quota_exceeded`, `config_error`, `internal_error`)
- `error_detail` curto, sem segredos
- Runtime `/execute` inclui também: `question_len` e `question_sha256`

### 2) Correlação

Header padrão: `X-Request-Id`.
- Runtime: usa valor recebido; se ausente, gera `uuid4`.
- Runtime propaga `X-Request-Id` para o Control Plane.
- Control Plane: usa valor recebido; se ausente, gera `uuid4`.

### 3) Configuração do sink + retenção mínima

Precedência da configuração:
1. `CONTRACTOR_AUDIT_CONFIG_JSON`
2. `CONTRACTOR_AUDIT_CONFIG_PATH`
3. `data/audit/audit.yaml`

Schema mínimo:
```json
{
  "enabled": true,
  "sink": "stdout",
  "file_path": "data/audit/audit.log.jsonl",
  "retention_days": 7
}
```

Regras:
- `enabled=false`: não emite e não quebra fluxo.
- `enabled=true` com config ausente/inválida: fail-closed (HTTP 500).
- `sink=file` com erro de escrita: fail-closed (HTTP 500).
- Rotação diária para arquivo: `audit.log.jsonl` → `audit-YYYY-MM-DD.log.jsonl`.
- Retenção mínima aplicada apenas em `sink=file`, com remoção de arquivos mais antigos que `retention_days`.

### 4) Redaction e privacidade

- Nunca registrar `Authorization`, `X-Api-Key`, tokens ou chaves.
- Nunca registrar payload bruto completo.
- No Runtime `/execute`, não registrar `question` em texto puro; registrar apenas:
  - `question_len`
  - `question_sha256`

### 5) Mapeamento determinístico de erro

- `401` → `unauthorized`
- `403` → `forbidden`
- `429` + `Rate limit exceeded` → `rate_limit_exceeded`
- `429` + `Quota exceeded` → `quota_exceeded`
- `500` por erro de configuração (Runtime/Auth/Audit config) → `config_error`
- Demais casos → `internal_error`

---

## Consequências

- A auditoria passa a ser parte obrigatória de governança quando habilitada.
- O sistema mantém rastreabilidade end-to-end por `request_id`.
- O contrato é mínimo e explícito, sem dependências adicionais e sem inferência heurística.

---

## Fora de escopo

- Integrações com SIEM externo
- Tracing distribuído completo
- Pipelines de observabilidade avançada (ADR 0018)
