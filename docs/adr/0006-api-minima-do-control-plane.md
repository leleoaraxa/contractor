# ADR 0006 — API mínima do Control Plane

## Contexto
O CONTRACTOR é um Control Plane para sistemas de IA governados. Para cumprir seu papel,
ele precisa expor uma **API mínima**, estável e bem definida, que permita:

- publicar bundles imutáveis,
- executar quality gates,
- promover e fazer rollback de bundles por tenant,
- resolver bundles ativos para execução em runtime,
- consultar trilhas de auditoria.

Sem uma API mínima explícita:
- implementações ficam inconsistentes,
- contratos entre Control Plane e Runtime ficam implícitos,
- governança depende de convenção e não de arquitetura.

Este ADR define **o conjunto mínimo de endpoints e responsabilidades da API do Control Plane (v1)**,
suficiente para operar o núcleo do CONTRACTOR sem escopo de produto ou UX.

## Opções consideradas
- API rica e extensa desde o início
- API genérica e flexível sem contratos claros
- **API mínima prescritiva, focada em governança (v1)**

## Decisão
Adotar uma **API mínima do Control Plane**, composta por endpoints explícitos e
bem delimitados, cobrindo apenas as capacidades essenciais de governança.

A API:
- é **orientada a recursos governados** (tenant, bundle, alias, audit),
- não executa lógica de domínio do sistema de IA,
- não expõe atalhos para alterar produção fora do fluxo de promoção,
- serve tanto operadores humanos quanto CI/CD e runtimes.

## Recursos e endpoints (conceituais)

### 1) Bundles

#### Publicar bundle
- `POST /tenants/{tenant_id}/bundles`
- Responsabilidade:
  - receber bundle completo,
  - validar estrutura mínima (ADR 0005),
  - calcular `bundle_id` imutável,
  - armazenar bundle,
  - registrar auditoria de publicação.

Resultado:
- bundle publicado (não promovido)
- `bundle_id` retornado

---

#### Listar bundles
- `GET /tenants/{tenant_id}/bundles`
- Responsabilidade:
  - listar bundles disponíveis para o tenant,
  - retornar metadados (bundle_id, versão lógica, status em gates).

---

### 2) Quality gates

#### Executar gates
- `POST /tenants/{tenant_id}/bundles/{bundle_id}/gates`
- Responsabilidade:
  - executar suites e validações configuradas,
  - registrar resultados detalhados,
  - atualizar estado do bundle (aprovado/reprovado).

---

#### Consultar resultado de gates
- `GET /tenants/{tenant_id}/bundles/{bundle_id}/gates`
- Responsabilidade:
  - retornar histórico e status atual dos gates.

---

### 3) Promoção e aliases

#### Promover bundle
- `POST /tenants/{tenant_id}/aliases/{alias}`
- Payload:
  - `bundle_id`

- Responsabilidade:
  - validar regras de promoção (gates OK, permissões),
  - atualizar alias (`draft`, `candidate`, `current`),
  - registrar auditoria.

---

#### Consultar aliases
- `GET /tenants/{tenant_id}/aliases`
- Responsabilidade:
  - retornar mapeamento atual de aliases → bundle_id.

---

### 4) Resolução para runtime

#### Resolver bundle ativo
- `GET /tenants/{tenant_id}/resolve/{alias}`
- Responsabilidade:
  - resolver alias para `bundle_id`,
  - retornar metadados mínimos e digest,
  - permitir cache seguro no runtime.

Regras:
- runtime **não resolve diretamente bundle_id arbitrário**,
- apenas aliases permitidos.

---

### 5) Auditoria

#### Consultar auditoria
- `GET /tenants/{tenant_id}/audit`
- Filtros:
  - tipo de evento,
  - intervalo de tempo,
  - bundle_id (opcional).

Responsabilidade:
- expor trilha de auditoria mínima para diagnóstico e compliance.

---

## Autenticação e autorização (v1)
- API do Control Plane exige autenticação forte (ex.: token de serviço ou usuário).
- Autorização é **tenant-aware**:
  - nenhum endpoint pode operar fora do tenant autenticado.
- Diferenciação de perfis (admin/operator/ci) é permitida, mas não obrigatória na v1.

Detalhes de authn/authz serão refinados em ADR específico.

## Regras explícitas
- Nenhum endpoint altera produção diretamente sem passar por aliases.
- Nenhum endpoint executa runtime de IA.
- Nenhum endpoint aceita mutação de bundle existente.
- Toda ação relevante gera evento de auditoria.
- Quebra de contrato da API é considerada mudança breaking.

## Consequências

### Ganhos
- Contrato claro entre Control Plane, CI e Runtime
- Base sólida para implementação incremental
- Governança explícita por design
- Facilita testes de integração e automação

### Custos
- Overhead inicial de definição de contratos
- Menor flexibilidade ad-hoc

### Fora do escopo (v1)
- UX / UI
- Billing
- Multi-environment avançado (dev/staging/prod)
- Webhooks e automações externas

## Status
- Aprovado como API mínima do Control Plane (v1)
- Qualquer expansão exige novo ADR
