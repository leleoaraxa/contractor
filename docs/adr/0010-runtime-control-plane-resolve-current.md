# ADR 0010 — Integração Runtime ↔ Control Plane: resolução do alias `current` via HTTP (fail-closed)

**Status:** Accepted
**Data:** 2026-02-05
**Decide:** Arquitetura de integração Runtime ↔ Control Plane
**Relacionados:** ADR 0001, ADR 0003, ADR 0006, ADR 0007, ADR 0008

---

## Contexto

O CONTRACTOR define, desde os ADRs fundacionais, a separação explícita entre **Control Plane** e **Runtime**
(ADR 0001). O Runtime executa bundles governados e o Control Plane é responsável por decisões de
publicação, promoção e resolução de versões.

Atualmente, em fase de bootstrap, o Runtime resolve o bundle ativo (`current`) por meio de
configuração local via alias config. Esse mecanismo é suficiente para demo e testes, mas **não
materializa o contrato arquitetural definido** nos ADRs:

- ADR 0003 define aliases (`draft`, `candidate`, `current`) por tenant.
- ADR 0006 define a existência de uma API mínima do Control Plane.
- ADR 0007 estabelece que o Runtime deve resolver o bundle ativo via Control Plane.
- ADR 0008 exige comportamento **fail-closed** em cenários de erro ou incompatibilidade.

Para avançar da fase de bootstrap para um sistema governado real, é necessário definir **como**
o Runtime resolve o alias `current` consultando o Control Plane, quais garantias são exigidas,
e como o sistema se comporta em caso de falha.

---

## Decisão a ser tomada

Definir o **contrato de integração HTTP** entre Runtime e Control Plane para a resolução do alias
`current`, incluindo:

- endpoint e payload mínimo,
- política de erro e indisponibilidade,
- comportamento de cache,
- garantias de fail-closed,
- responsabilidades claras entre Runtime e Control Plane.

---

## Opções consideradas

### Opção A — Runtime resolve `current` via HTTP no Control Plane (fail-closed)

O Runtime realiza uma chamada HTTP síncrona ao Control Plane para resolver o alias `current`
antes de executar uma requisição.

**Fluxo:**
1. Runtime recebe `/execute`.
2. Runtime chama o Control Plane:
```

GET /tenants/{tenant_id}/resolve/current

```
3. Control Plane retorna metadados do bundle promovido.
4. Runtime valida resposta e prossegue com a execução.

**Características:**
- Fail-closed: qualquer erro impede a execução.
- Fonte única de verdade: Control Plane decide o bundle ativo.
- Alinhamento total com ADR 0003, 0006 e 0007.

**Prós:**
- Governança forte e explícita.
- Evita execução de bundles não promovidos.
- Auditoria clara e centralizada.

**Contras:**
- Introduz dependência de rede no caminho crítico.
- Requer política clara de timeout e indisponibilidade.

---

### Opção B — Runtime usa cache local com fallback em alias config

O Runtime consulta o Control Plane, mas mantém cache local e permite fallback em alias config
em caso de erro.

**Prós:**
- Maior resiliência operacional.
- Menor impacto de indisponibilidade do Control Plane.

**Contras:**
- Viola o princípio fail-closed do ADR 0008.
- Pode executar bundles não mais promovidos.
- Introduz ambiguidade de fonte de verdade.

---

### Opção C — Control Plane empurra atualizações para o Runtime (push)

O Control Plane notifica o Runtime sempre que o alias `current` muda.

**Prós:**
- Baixa latência em execução.
- Runtime não depende de chamadas síncronas.

**Contras:**
- Complexidade elevada (coordenação, estado, reconciliação).
- Fora do escopo da fase atual do produto.
- Não elimina a necessidade de contrato HTTP inicial.

---

## Decisão

**Escolher a Opção A.**

O Runtime deve resolver o alias `current` **exclusivamente via Control Plane**, por chamada HTTP,
com comportamento **fail-closed** em qualquer cenário de erro.

Esta decisão prioriza governança, previsibilidade e alinhamento estrito com os ADRs fundacionais,
aceitando a complexidade operacional como custo necessário.

---

## Contrato mínimo proposto

### Endpoint (Control Plane)

```

GET /tenants/{tenant_id}/resolve/current

````

### Resposta mínima (exemplo)

```json
{
  "bundle_id": "demo-faq-0001",
  "runtime_compatibility": {
    "min_version": "1.0.0"
  }
}
````

> Campos adicionais podem ser definidos em ADRs futuros, sem quebrar este contrato mínimo.

---

## Comportamento do Runtime

* **Timeout ou erro HTTP:** abortar execução (fail-closed).
* **Payload inválido:** abortar execução.
* **Incompatibilidade de runtime:** abortar execução.
* **Resposta válida:** prosseguir com execução.

Nenhuma execução deve ocorrer sem resolução bem-sucedida do alias `current`.

---

## Consequências

### Positivas

* Materializa o contrato definido no ADR 0007.
* Estabelece o Control Plane como fonte única de verdade.
* Base sólida para promotion, rollback, auditoria e gates.

### Negativas

* Aumenta acoplamento operacional entre Runtime e Control Plane.
* Exige observabilidade e SLOs mínimos no Control Plane (tratados em ADR 0018).

---

## Fora de escopo

Este ADR **não** define:

* Autenticação/autorização da chamada (ADR 0011 / 0012).
* Download ou distribuição de bundles (ADR 0017).
* Workflow de promoção e rollback (ADR 0019).
* Quality gates (ADR 0016).
* Auditoria detalhada (ADR 0014).

---

## Próximos passos

1. Implementar endpoint `resolve/current` no Control Plane (ADR 0006).
2. Implementar chamada HTTP no Runtime conforme este ADR.
3. Criar testes E2E Runtime ↔ Control Plane (mockado).
4. Atualizar `docs/STATUS.md` ao promover este ADR para `Accepted`.
