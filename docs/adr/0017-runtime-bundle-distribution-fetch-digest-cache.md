# ADR 0017 — Distribuição de bundles para o Runtime (fetch, digest e cache local)

**Status:** Draft  
**Data:** 2026-02-05  
**Relacionados:** ADR 0002, ADR 0005, ADR 0010, ADR 0011, ADR 0012, ADR 0013, ADR 0014

---

## Contexto

O Runtime já resolve `bundle_id` via Control Plane e já executa bundles no layout do repositório.
Ainda não havia contrato explícito para garantir presença local determinística do bundle quando o Control Plane aponta para um `bundle_id`.

Este ADR define o contrato mínimo v1 para fetch, digest, cache local e integração com auditoria, sem alterar o layout interno dos bundles.

---

## Decisão

### 1) Resolução de caminho local

O Runtime considera apenas este caminho local canônico:

```text
data/bundles/{bundle_id}/
```

Regras:

- `{bundle_id}` é o nome do diretório local do bundle.
- O diretório deve conter `manifest.yaml` e a estrutura mínima esperada (`data/`, `entities/`, `metadata/`, `ontology/`, `policies/`, `suites/`, `templates/`).
- Diretório existente e válido = `bundle_cache.status = "hit"`.
- Diretório ausente = `bundle_cache.status = "miss"`.

Não há inferência de aliases nem reescrita de paths internos para esta etapa.

### 2) Fetch em cache miss

Quando `data/bundles/{bundle_id}/` não existe:

- Runtime monta URL do artefato a partir de:
  - `CONTRACTOR_BUNDLE_BASE_URL`
  - `/{bundle_id}.tar.gz`
- Download é feito para diretório temporário.
- Não há retries automáticos.

### 3) Digest, unpack e validação estrutural

Fluxo v1 obrigatório:

1. Download para arquivo temporário.
2. Cálculo de `sha256` do arquivo.
3. Comparação com digest esperado (`bundle_sha256`) recebido da resolução no Control Plane.
4. Em mismatch de digest: falha imediata.
5. Extração segura (`tar.gz`) para diretório temporário.
6. Validação da estrutura obrigatória do bundle.
7. Move atômico para `data/bundles/{bundle_id}/`.
8. Marcação do conteúdo local como somente leitura (quando aplicável no filesystem).

Não sobrescreve bundle já existente.

### 4) Ordem do `/execute`

1. Autenticação Runtime (ADR 0012).
2. Rate limit/quota (ADR 0013).
3. Resolve `bundle_id` no Control Plane (ADR 0010).
4. Garante bundle local (hit/miss + fetch/verify/unpack no miss).
5. Executa pipeline com `data/bundles/{bundle_id}`.
6. Emite auditoria (ADR 0014).

### 5) Auditoria

Reuso do evento `execute` já existente no Runtime, adicionando bloco opcional:

```json
"bundle_cache": {
  "status": "hit" | "miss",
  "bundle_id": "demo-faq-0001"
}
```

Regras:

- Exatamente 1 evento por chamada `/execute`.
- `request_id` obrigatório.
- Fail-closed: falha de auditoria retorna 500.
- Não loga URL de origem de bundle, paths locais completos nem payload bruto de bundle.

### 6) Contrato de erro

| Situação                            | HTTP |
| ----------------------------------- | ---- |
| Bundle não encontrado na origem     | 503  |
| Download falhou                     | 503  |
| Digest inválido                     | 500  |
| Estrutura inválida após unpack      | 500  |
| Bundle incompatível (`min_version`) | 500  |

Sem retries e sem fallback alternativo.

---

## Consequências

### Positivas

- Contrato explícito de presença local de bundle no Runtime.
- Integridade mínima garantida por digest.
- Reuso determinístico de cache local por `bundle_id`.
- Observabilidade mínima de hit/miss sem vazar dados sensíveis.

### Trade-offs

- Sem GC/eviction/versionamento avançado na v1.
- Dependência do fornecimento de digest no caminho de distribuição remota.

---

## Fora de escopo

- `data/runtime/bundles`
- Duplicação de bundles já existentes
- Mudança no layout interno de `data/bundles/*`
- CDN, S3, storage externo
- GC/eviction/versionamento avançado
- Mudanças em auth/rate limit/auditoria além da integração mínima definida

---

## Implementação v1 associada

- Runtime com `ensure_local_bundle` para hit/miss, fetch, digest e unpack.
- Control Plane passa `bundle_sha256` opcional quando configurado.
- Evento de auditoria do Runtime inclui `bundle_cache.status` em execução com resolução via Control Plane.
