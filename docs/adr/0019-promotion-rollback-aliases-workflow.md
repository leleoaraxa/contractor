# ADR 0019 — Promoção e rollback v1 (workflow de aliases e invariantes)

**Status:** Draft
**Data:** 2026-02-06
**Decide:** Workflow v1 de promoção e rollback no Control Plane usando aliases (`candidate`, `current`) com invariantes explícitas e auditoria obrigatória
**Relacionados:** ADR 0003, ADR 0004, ADR 0006, ADR 0016, ADR 0017

---

## Contexto

O ADR 0003 define o conceito de aliases por tenant (`draft`, `candidate`, `current`) para permitir promoção e rollback de bundles sem mutação do artefato.

Até o momento, o projeto já possui:

* bundles imutáveis com identificação clara (ADR 0002);
* distribuição e cache de bundles no Runtime (ADR 0017);
* quality gates v1 executáveis e persistidos no Control Plane (ADR 0016);
* autenticação, autorização e auditoria end-to-end v1 (ADR 0011, ADR 0014).

Porém, ainda não existe um **workflow formalizado e governado** para:

* promover bundles aprovados,
* realizar rollback explícito,
* garantir invariantes operacionais,
* registrar auditoria consistente dessas transições.

Sem esse contrato, aliases permanecem apenas configuração estática, sem governança.

---

## Decisão

Definir um **workflow v1 explícito, determinístico e auditável** de promoção e rollback de bundles no Control Plane, baseado em aliases por tenant.

O v1 prioriza **governança e clareza**, não automação.

---

## Escopo do v1

* O Control Plane governa **apenas os aliases `candidate` e `current`**.
* O alias `draft` permanece fora do escopo do Control Plane no v1 (responsabilidade de build/publish).
* Promoção e rollback são **operações explícitas**, síncronas e auditadas.
* Nenhum efeito colateral direto no Runtime (pull-based).

---

## Modelo de estado (v1)

Para cada `tenant_id`, o Control Plane mantém o estado:

```json
{
  "tenant_id": "tenant_a",
  "aliases": {
    "candidate": {
      "bundle_id": "bundle-xyz"
    },
    "current": {
      "bundle_id": "bundle-abc"
    }
  }
}
```

* Persistência local v1 (ex.: JSON com escrita atômica).
* Estrutura é **fonte de verdade** para resolução de aliases.

---

## Gate aprovado (definição v1)

Um bundle é considerado **aprovado** para um tenant quando:

* existe **ao menos um** resultado de gate persistido com:

  * `tenant_id` correspondente,
  * `bundle_id` correspondente,
  * `outcome = pass`.

Não há no v1:

* janela temporal,
* scoring,
* prioridade entre gates.

---

## Transições permitidas (v1)

### 1) Definir candidate

* Operação administrativa para preparar promoção.
* Não altera `current`.

```
candidate <- bundle_id
```

Regras:

* `bundle_id` **deve existir**.
* Operação idempotente.

---

### 2) Promoção (candidate → current)

```
current <- candidate
```

Regras obrigatórias:

* MUST: `candidate` deve estar definido.
* MUST: bundle apontado por `candidate` deve ter **gate aprovado**.
* MUST: operação ser **idempotente**.
* MUST: atualizar apenas alias (sem mutar bundle).
* MUST: emitir auditoria.

Resultado:

* `current` passa a apontar para o bundle de `candidate`.

---

### 3) Rollback explícito (v1)

Rollback ocorre apontando explicitamente para um bundle conhecido:

```
current <- target_bundle_id
```

Regras obrigatórias:

* MUST: `target_bundle_id` deve existir.
* MUST: `target_bundle_id` deve ter **gate aprovado**.
* MUST: rollback ser **explícito** (nenhum rollback automático).
* MUST: operação ser **idempotente**.
* MUST: emitir auditoria.

---

## Invariantes operacionais (v1)

### Autenticação e tenant

* MUST: `X-Tenant-Id` deve coincidir com `{tenant_id}` do path.
* MUST: token deve mapear para exatamente um tenant.
* MUST NOT: permitir operação cross-tenant.

### Promoção e rollback

* MUST: `current` **só pode mudar** via promoção ou rollback governados.
* MUST: `current` **nunca** pode apontar para bundle sem gate aprovado.
* MUST: transições inválidas devem falhar explicitamente.
* MUST NOT: alterar aliases fora das transições definidas.

### Auditoria

* MUST: cada operação de promoção ou rollback gera **1 evento**.
* MUST: falha de auditoria resulta em erro (`fail-closed`).

### Runtime

* MUST: Control Plane **não** chama Runtime diretamente.
* MUST: Runtime resolve alias de forma pull-based no próximo ciclo.

---

## Endpoints esperados (referência)

*(Os endpoints serão definidos/implementados após este ADR, mas o contrato lógico é este)*

* `POST /tenants/{tenant_id}/aliases/candidate`
* `POST /tenants/{tenant_id}/aliases/promote`
* `POST /tenants/{tenant_id}/aliases/rollback`

---

## Contratos de erro v1

* **401 / 403** — autenticação/autorização inválida.
* **404** — tenant inexistente ou bundle inexistente.
* **409** — transição inválida (ex.: promover sem candidate definido).
* **422** — payload inválido.
* **500** — falha interna, configuração ausente ou auditoria inválida (fail-closed).

---

## Auditoria v1

Cada operação emite **1 evento** no Control Plane:

* `event`: `alias_promote` | `alias_rollback`
* `tenant_id`
* `from_bundle_id`
* `to_bundle_id`
* `request_id`
* `outcome`
* `http_status`
* `latency_ms`

Não registrar payload completo nem histórico completo de aliases no evento.

---

## Fora de escopo (v1)

* Promoção automática baseada em gates.
* Rollback automático.
* Ambientes múltiplos.
* Observabilidade avançada.
* Persistência distribuída.
* Integração direta com Runtime.

---

## Consequências

### Positivas

* Promoção e rollback deixam de ser configuração manual.
* Invariantes claras impedem estados inválidos.
* Base sólida para automação futura (ADR posterior).

### Trade-offs

* Operações são manuais e síncronas.
* Persistência local é suficiente para v1, mas limitada.

---

## Próximos passos

1. Implementar endpoints v1 de promoção e rollback no Control Plane.
2. Adicionar testes determinísticos cobrindo invariantes.
3. Promover este ADR para **Accepted** após validação.
4. Evoluir automação no futuro sem quebrar contratos aceitos.

