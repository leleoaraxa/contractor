# ADR 0011 — Autenticação e autorização v1 do Control Plane

**Status:** Draft
**Data:** 2026-02-XX
**Decide:** Modelo de autenticação e autorização da API do Control Plane
**Relacionados:** ADR 0001, ADR 0003, ADR 0004, ADR 0006, ADR 0010

---

## Contexto

O CONTRACTOR define, desde os ADRs fundacionais, a separação explícita entre **Control Plane** e **Runtime**
(ADR 0001). O ADR 0006 define a **API mínima do Control Plane** e o ADR 0010 (Accepted) materializa a
integração Runtime ↔ Control Plane para resolução do alias `current`, tornando o Control Plane a **fonte única
de verdade** para a decisão de bundle ativo.

Até este ponto, no bootstrap, não há um contrato explícito e verificável de:

- **quem** pode chamar a API do Control Plane,
- **como** autenticar chamadas,
- **como** autorizar operações de forma estritamente **tenant-aware**.

Isso cria ambiguidade operacional e enfraquece as garantias de governança/isolamento esperadas para um Control
Plane.

---

## Decisão a ser tomada

Definir o mecanismo mínimo (v1) de **autenticação (authn)** e **autorização (authz)** para todos os endpoints do
Control Plane, garantindo:

- autenticação obrigatória para toda requisição,
- autorização estrita por tenant (sem acesso cross-tenant),
- comportamento **fail-closed** em ausência/invalidade de credenciais ou configuração.

---

## Opções consideradas

### Opção A — API keys por tenant (header-based, estático)

Cada tenant possui uma chave (ou conjunto mínimo de chaves) para o Control Plane, enviada por header.

**Headers:**

```
Authorization: Bearer <control_plane_token>
X-Tenant-Id: <tenant_id>
```

**Prós:**
- Implementação simples, auditável e determinística.
- Adequado ao estágio atual (bootstrap) sem dependências externas.
- Permite evolução posterior (JWT/mTLS) via novos ADRs.

**Contras:**
- Rotação manual.
- Não define RBAC fino (papéis/permissões) na v1.

---

### Opção B — JWT com claims (tenant_id/role)

Tokens JWT assinados com claims de tenant e papel.

**Prós:**
- Base para RBAC e integrações futuras.

**Contras:**
- Complexidade desnecessária na fase atual.
- Requer infraestrutura de assinatura/validação e gestão de chaves.

---

### Opção C — mTLS

Autenticação por certificados de cliente.

**Prós:**
- Segurança forte.

**Contras:**
- Alto custo operacional e fora do escopo do bootstrap.

---

## Decisão

**Escolher a Opção A — API keys por tenant (v1).**

O Control Plane deve exigir autenticação obrigatória por token estático por tenant e autorização estrita por
tenant em **todos** os endpoints expostos.

---

## Contrato mínimo (v1)

### Headers obrigatórios

```
Authorization: Bearer <control_plane_token>
X-Tenant-Id: <tenant_id>
```

### Regras de autenticação (authn)

- `Authorization` ausente ou malformado → **401 Unauthorized**
- token inválido/desconhecido → **401 Unauthorized**
- configuração de tokens ausente/inválida → **500 Internal Server Error** (fail-closed)

### Regras de autorização (authz)

- token pertence a **exatamente um tenant**
- `X-Tenant-Id` deve coincidir com o tenant do token
- endpoints com `tenant_id` no path devem validar coerência:
  - `tenant_id` do path deve coincidir com `X-Tenant-Id` (e, portanto, com o tenant do token)
- mismatch → **403 Forbidden**
- nenhuma operação cross-tenant é permitida

---

## Aplicação aos endpoints

Este contrato aplica-se a **todos** os endpoints do Control Plane, incluindo o endpoint mínimo já definido no
ADR 0010:

```
GET /tenants/{tenant_id}/resolve/current
```

Para este endpoint:
- `tenant_id` (path) == `X-Tenant-Id` == tenant do token
- caso contrário, a resposta deve ser **403 Forbidden**

---

## Configuração (bootstrap)

O mecanismo de keys v1 deve ser configurável sem hardcode em código-fonte. Formas aceitas:

- via arquivo (ex.: `data/control_plane/tenants.json`)
- e/ou via variável de ambiente (string JSON)

O formato do arquivo/JSON deve ser simples e determinístico, por exemplo:

```json
{
  "tenants": {
    "tenant_a": {"token": "cp_test_key_a"},
    "tenant_b": {"token": "cp_test_key_b"}
  }
}
```

> Detalhes exatos de nomes de env vars e path default devem ser definidos pela implementação, mantendo o princípio
> “sem hardcode de domínio” e permitindo override por ambiente.

---

## Auditoria (mínimo)

Este ADR exige apenas a garantia de que chamadas autenticadas possam ser auditadas no futuro (ADR 0014).
O formato completo e retenção serão definidos no ADR 0014.

---

## Consequências

### Positivas
- Elimina ambiguidade de segurança na API do Control Plane.
- Garante isolamento por tenant (tenant-aware) com regra simples e verificável.
- Permite uso seguro por Runtime, CI e operadores.

### Negativas
- Rotação/gestão de tokens manual na v1.
- Sem RBAC fino nesta etapa.

---

## Fora de escopo

Este ADR não define:
- JWT/OAuth/SSO/mTLS
- RBAC avançado
- gestão de segredos e rotação automática
- autenticação do Runtime para seu próprio `/execute` (ver ADR 0012)

---

## Próximos passos

1. Implementar validação de `Authorization`  `X-Tenant-Id` no Control Plane.
2. Aplicar authn/authz a todos os endpoints do Control Plane (incluindo `resolve/current`).
3. Atualizar a integração do Runtime → Control Plane para enviar os headers exigidos.
4. Adicionar testes cobrindo casos 401/403/200.
5. Atualizar `docs/STATUS.md` e promover este ADR para **Accepted** quando estiver 100% materializado e testado.
