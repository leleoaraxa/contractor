# ADR 0016 — Quality gates v1 (suites, execução e critérios de promoção)

**Status:** Draft  
**Data:** 2026-02-06  
**Decide:** Contrato executável mínimo de quality gates no Control Plane  
**Relacionados:** ADR 0005, ADR 0006, ADR 0009, ADR 0014, ADR 0017, ADR 0019

---

## Contexto

O CONTRATOR já possui:

- modelo mínimo de bundle com suites dentro do próprio bundle (ADR 0005);
- API mínima do Control Plane definindo endpoints de gates (ADR 0006);
- caso canônico FAQ determinístico com suite golden (ADR 0009);
- correlação por `request_id` e auditoria end-to-end (ADR 0014);
- Runtime e distribuição de bundle já aceitos (ADR 0017).

Porém, faltava um contrato **executável v1** de gates no Control Plane. Sem isso,
"gates" permanecem conceito sem endpoint/resultado persistido/auditoria específica.

---

## Decisão

Implementar quality gates v1 no Control Plane com escopo mínimo e determinístico.

### 1) Endpoints v1 (ADR 0006)

- `POST /tenants/{tenant_id}/bundles/{bundle_id}/gates`
  - executa suites do bundle;
  - aceita `X-Request-Id` e propaga para execução interna;
  - retorna resultado final (sincrônico, `status=completed`).
- `GET /tenants/{tenant_id}/bundles/{bundle_id}/gates/{gate_id}`
  - retorna resultado persistido de um gate específico.
- `GET /tenants/{tenant_id}/bundles/{bundle_id}/gates/history`
  - retorna histórico resumido dos últimos N gates persistidos.

Autenticação/autorização reutiliza contrato atual do Control Plane (ADR 0011).

### 2) Suite schema v1 suportado (as-is do bundle atual)

O schema real observado em `data/bundles/**/suites/*.json` (hoje: `demo/faq/suites/faq_golden.json`) é:

- arquivo JSON do tipo `array` não-vazio;
- cada item é objeto com campos obrigatórios:
  - `tenant_id: string não-vazia`
  - `question: string não-vazia`
  - `expected_answer: string não-vazia`

v1 suporta **somente** esse formato. Suites são **tenant-scoped**; o Control Plane rejeita cases cross-tenant (`422 Suite invalid`).

### 3) Execução determinística v1

- Sem rede externa e sem `sleep`.
- Para cada caso da suite, o Control Plane executa Runtime in-process via `fastapi.testclient.TestClient` chamando `POST /execute`.
- `X-Request-Id` do POST de gate é preservado e cada caso recebe request id derivado:
  - `{request_id}:case:{i}`.
- Critério de comparação v1:
  - `pass` quando `output_text` retornado pelo Runtime é exatamente igual a `expected_answer`.

### 4) Critérios de aprovação v1

- Regra única de aprovação: **100% dos casos devem passar**.
- Tolerância: **nenhuma** (`max_failures = 0`).
- Se qualquer caso falhar, `outcome = fail`.

### 5) Persistência mínima v1

- Armazenamento local sem banco:
  - `data/control_plane/gates/{tenant_id}/{bundle_id}/{gate_id}.json`
- Escrita atômica (`.tmp` + `replace`).
- `history` lista no máximo **50** execuções mais recentes por `mtime`.

### 6) Formato mínimo do resultado persistido

Campos mínimos:

- `gate_id`, `request_id`, `tenant_id`, `bundle_id`
- `status` (`completed`)
- `outcome` (`pass` | `fail`)
- `created_at` (UTC ISO)
- `criteria` (`pass_rule=all_cases_must_pass`, `max_failures=0`)
- `summary` (`total`, `passed`, `failed`)
- `suites[]` com:
  - `suite_id`, `total`, `passed`, `failed`, `outcome`
  - `cases[]` com `case_index`, `tenant_id`, `request_id`, `outcome`, `http_status`

### 7) Auditoria v1 (ADR 0014)

Cada execução de gate emite **1 evento** `quality_gate_run` no Control Plane com:

- `request_id`, `tenant_id`, `bundle_id`, `gate_id`
- `outcome`, `http_status`, `latency_ms`
- `summary` agregado (`total`, `passed`, `failed`)

Não registrar payload completo de suite nem resposta completa do Runtime no evento.

---

## Contratos de erro v1

- **Bundle inexistente**: `404 Bundle not found`
- **Suite inválida** (JSON inválido/schema divergente): `422 Suite invalid`
- **Falha interna de execução** (Runtime erro interno, chave tenant ausente, etc.): `500`
- **Config faltante/inválida** (auth/audit/runtime config): `500` fail-closed

---

## Fora de escopo (v1)

- Promotion/rollback governado por gate (fica para ADR 0019)
- Gates assíncronos/distribuídos
- Thresholds estatísticos, scoring, flaky handling
- Tipos adicionais de suite além do formato FAQ canônico
- Persistência em banco/objeto remoto

---

## Consequências

### Positivas

- Gate deixa de ser conceito e vira contrato executável mínimo.
- Rastreabilidade ponta-a-ponta com `request_id` derivado por caso.
- Base para workflow de promoção do ADR 0019 sem alterar contratos aceitos.

### Trade-offs

- Execução sincrônica pode ficar lenta para suites grandes.
- Persistência local é suficiente para v1, mas limitada para multi-instância.

---

## Próximos passos

1. Evoluir para vínculo de promoção (ADR 0019).
2. Definir tipos adicionais de suite mantendo determinismo.
3. Avaliar backend de persistência compartilhado quando houver necessidade operacional.
