# ADR 0012 — Autenticação v1 do Runtime (chaves por tenant e validação de headers)

**Status:** Draft
**Data:** 2026-02-XX
**Decide:** Contrato de autenticação (authn) mínimo do Runtime (v1)
**Relacionados:** ADR 0001, ADR 0004, ADR 0007, ADR 0010, ADR 0011

---

## Contexto

O ADR 0007 define o Runtime como um executor governado e exige, como requisito mínimo de segurança (v1),
**autenticação obrigatória por tenant** e isolamento lógico.

O Runtime já expõe `POST /execute` e recebe `tenant_id` como parte do fluxo. Porém, sem um contrato de
authn explícito, o Runtime pode aceitar execuções sem controle tenant-aware, o que viola o contrato mínimo.

Além disso, com o ADR 0010 (Accepted), o Runtime chama o Control Plane para resolver `current`, e esta chamada
passa a depender de um modelo coerente de identidade/tenant entre as duas superfícies.

---

## Decisão a ser tomada

Definir o contrato mínimo (v1) de autenticação do Runtime para `POST /execute`, incluindo:

- headers mínimos,
- regras de rejeição (erro seguro),
- origem/configuração das chaves por tenant (sem hardcode),
- invariantes de isolamento tenant-aware.

---

## Opções consideradas

### Opção A — API keys por tenant (header-based, estático)

**Headers:**

```
X-Tenant-Id: <tenant_id>
X-Api-Key: <tenant_api_key>
```

**Prós:**
- Simples, determinístico e auditável.
- Compatível com bootstrap (sem dependências externas).

**Contras:**
- Rotação manual.
- Sem RBAC fino.

---

### Opção B — JWT no Runtime

**Prós:**
- Base para RBAC e claims.

**Contras:**
- Complexidade desnecessária no bootstrap.

---

## Decisão

**Escolher a Opção A — API keys por tenant (v1).**

O Runtime deve exigir headers `X-Tenant-Id` e `X-Api-Key` para executar `POST /execute`, rejeitando qualquer
requisição sem autenticação válida.

---

## Contrato mínimo (v1)

### Headers obrigatórios

```
X-Tenant-Id: <tenant_id>
X-Api-Key: <tenant_api_key>
```

### Regras (authn)

- header ausente → **401 Unauthorized**
- tenant desconhecido → **403 Forbidden**
- chave inválida para o tenant → **403 Forbidden**
- configuração de chaves ausente/inválida → **500 Internal Server Error** (fail-closed)

### Invariantes (isolamento)

- O `tenant_id` autenticado é a identidade usada para:
  - resolução de `current` no Control Plane (ADR 0010),
  - auditoria mínima de execução (ADR 0004),
  - aplicação de políticas (ex.: rate limiting) quando materializadas (ADR 0013).

O Runtime não deve permitir execução com `tenant_id` implícito ou inferido.

---

## Configuração (bootstrap)

O mecanismo de keys v1 deve ser configurável sem hardcode em código-fonte. Formas aceitas:

- arquivo (ex.: `data/runtime/tenants.json`)
- e/ou variável de ambiente (string JSON)

O formato deve ser simples e determinístico, por exemplo:

```json
{
  "tenant_a": "runtime_test_key_a",
  "tenant_b": "runtime_test_key_b"
}
```

---

## Auditoria (mínimo)

Toda requisição autenticada ao Runtime deve ser auditável conforme ADR 0004 (detalhes completos em ADR 0014).

---

## Consequências

### Positivas
- Fecha o requisito de “autenticação por tenant” do ADR 0007 de forma mínima e verificável.
- Simplifica testes e operação no bootstrap.

### Negativas
- Rotação manual na v1.
- Sem RBAC fino.

---

## Fora de escopo

- JWT/OAuth/SSO/mTLS
- gestão de segredos e rotação automática
- autorização por papéis (RBAC)

---

## Próximos passos

1. Materializar `X-Tenant-Id` + `X-Api-Key` no Runtime e cobrir com testes.
2. Atualizar `docs/STATUS.md` ao promover este ADR para **Accepted**.
