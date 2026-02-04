# ARCHITECTURE — CONTRACTOR (v1)

## 1. Objetivo do documento
Este documento define a arquitetura mínima do CONTRACTOR, incluindo componentes, fronteiras de responsabilidade, fluxos, contratos e princípios operacionais. Ele é a referência técnica para evoluir o produto sem perder determinismo, governança e auditabilidade.

Fontes de verdade complementares:
- docs/PRODUCT.md
- docs/STATUS.md
- docs/adr/*


## 2. Visão de alto nível
O CONTRACTOR é um SaaS B2B que atua como **Control Plane para sistemas de IA governados**, com separação explícita entre:
- **Control Plane**: governa, versiona e promove artefatos (bundles) com políticas e quality gates.
- **Runtime**: executa pedidos em produção com base exclusivamente no bundle promovido (`current`) do tenant.

O objetivo é operar sistemas de IA como infraestrutura crítica: determinística, auditável, segura e multi-tenant.


## 3. Princípios arquiteturais (não negociáveis)
1. **Separação Control Plane / Runtime**
   - Control Plane não executa “trabalho de produção”.
   - Runtime não decide “o que é permitido”; ele aplica decisões já governadas.

2. **Imutabilidade por design**
   - Bundles são imutáveis.
   - Promoção troca aliases (ex.: `draft` → `candidate` → `current`), não “edita produção”.

3. **Determinismo e reprodutibilidade**
   - Uma execução deve ser reproduzível com: tenant + bundle_id + payload + políticas aplicadas + versão do runtime.
   - Mudanças de comportamento são rastreáveis por promoção.

4. **Governança antes da execução**
   - Políticas e quality gates são aplicados antes de qualquer bundle virar `current`.
   - Runtime executa somente sob governança ativa.

5. **Multi-tenancy e isolamento**
   - Isolamento lógico por tenant como baseline.
   - Sem vazamento de configuração/artefatos entre tenants.

6. **Auditabilidade e observabilidade de primeira classe**
   - Toda ação relevante gera trilha de auditoria.
   - Execução produz sinais operacionais (logs/metrics/traces) compatíveis com ambientes enterprise.

7. **Sem lógica hardcoded de domínio**
   - Domínio do sistema de IA governado deve residir em artefatos de bundle (ontologia, entidades, políticas, templates, suites etc.), não em código ad-hoc.

8. **Erro seguro**
   - Na dúvida: negar, degradar com segurança, ou responder com noop/erro explícito (nunca “chutar”).


## 4. Componentes e responsabilidades

### 4.1 Control Plane (SaaS)
Responsável por:
- Cadastro e gestão de tenants.
- Recebimento, validação e empacotamento de bundles.
- Armazenamento e versionamento de bundles (imutáveis).
- Execução de quality gates (suites e verificações).
- Promoção/rollback via aliases por tenant.
- Gestão de políticas operacionais (ex.: rate limits, ambientes permitidos, constraints).
- Auditoria de:
  - quem publicou bundle,
  - resultados de gates,
  - promoções/rollbacks,
  - configuração por tenant.

Não é responsável por:
- Servir tráfego de produção do sistema governado.
- Ajustar comportamento do runtime via “hotfix” manual sem promoção.

Interfaces típicas:
- API administrativa (tenant, bundle, promotion, audit)
- API de artefatos (download/resolve bundle por alias)


### 4.2 Runtime (execução)
Responsável por:
- Expor endpoint(s) de execução do sistema governado (ex.: `/ask`).
- Resolver bundle do tenant (normalmente alias `current`) e executar pipeline.
- Aplicar políticas “em runtime” que sejam determinísticas e configuradas (ex.: rate limiting, allowlist de ambiente, permissões por tenant).
- Registrar auditoria de execução e sinais operacionais.
- Manter execução read-only em relação aos artefatos (runtime não “edita” bundles).

Não é responsável por:
- Decidir o que vira produção (isso é do Control Plane).
- Aceitar configuração de domínio via código ou flags não versionadas no bundle.


### 4.3 Bundle (artefato imutável)
O bundle é o **contrato governado** do comportamento do sistema de IA. Ele encapsula:
- Ontologia e entidades (contratos e schema)
- Políticas (ex.: segurança, cache, rag, rate limit, allowlists)
- Templates (respostas, formatação, UX de narrativas quando aplicável)
- Suites de qualidade (routing/thresholds/golden tests etc.)
- Metadados de versão, compatibilidade e assinatura/integração com gates

Propriedades:
- Imutável, identificado por `bundle_id` (ex.: timestamp/semver + hash).
- Resolvido por alias: `draft`, `candidate`, `current` (por tenant).
- Passa por gates antes de chegar em `current`.


### 4.4 Quality Gates (governança)
Gates verificam se um bundle pode ser promovido. Exemplos de gates (conceituais):
- Validação estrutural do bundle (conteúdo obrigatório, schemas)
- Compatibilidade com versão do runtime
- Suites determinísticas: routing/thresholds/golden outputs
- Segurança: bloqueio de templates perigosos, políticas ausentes, etc.
- Política de release: “no regression”, “no misses”, etc. (quando aplicável)

Os gates são executados no Control Plane e registrados em auditoria.


### 4.5 Auditoria (control + runtime)
Auditoria é um subsistema transversal com dois tipos:
- **Change Audit (Control Plane):** mudanças de estado (publish bundle, gate result, promote/rollback, tenant config).
- **Execution Audit (Runtime):** execuções em produção (tenant, bundle_id, request_id, decisão de roteamento, entidade, policies, tempos, status).

Requisito: auditoria deve permitir responder “o que mudou”, “quando mudou”, “por quem” e “qual bundle gerou tal execução”.


## 5. Modelo de dados (conceitual)
Entidades centrais:

### 5.1 Tenant
- `tenant_id`
- status (active/suspended)
- políticas operacionais (ex.: limites)
- aliases para bundles (`draft`, `candidate`, `current`)
- metadados (ambiente, tags, etc.)

### 5.2 Bundle
- `bundle_id` (imutável)
- conteúdo (artefatos)
- `created_at`, `created_by`
- `compatibility` (mín. versão do runtime, etc.)
- `digest/hash`
- estado de gates (pass/fail) por suite/gate

### 5.3 Promotion/Alias
- `tenant_id`
- `alias`: draft|candidate|current
- `bundle_id`
- trilha: promoted_by, promoted_at, gate_snapshot_ref

### 5.4 Audit Log
- `event_id`
- `event_type` (publish_bundle, gate_pass, gate_fail, promote, rollback, runtime_exec, rate_limit_denied, etc.)
- `actor` (user/service)
- `tenant_id`
- `bundle_id` (quando aplicável)
- payload (mínimo necessário; com redaction quando aplicável)
- timestamps e correlacionadores (request_id/trace_id)


## 6. Fluxos principais (end-to-end)

### 6.1 Publish bundle
1) Usuário/CI envia bundle para o Control Plane
2) Control Plane valida estrutura e registra `bundle_id` imutável
3) Bundle fica disponível para gates e possível uso em `draft`

Saída:
- bundle armazenado e auditado
- `bundle_id` emitido
- estado: “publicado, não promovido”

### 6.2 Quality gate (candidate)
1) Control Plane executa gates/suites para um bundle
2) Registra resultados e artefatos (relatórios)
3) Se aprovado, permite setar alias `candidate`

Saída:
- gate report auditado
- bundle “promovível” (policy-based)

### 6.3 Promote candidate → current
1) Operador/CI solicita promoção do `candidate` para `current`
2) Control Plane verifica políticas (ex.: gates ok, janelas, permissões)
3) Control Plane troca alias `current` apontando para bundle_id aprovado
4) Auditoria registra promoção

Saída:
- produção passa a executar sob bundle `current` do tenant

### 6.4 Runtime execution (/ask ou equivalente)
1) Runtime recebe requisição com identificação de tenant
2) Resolve alias `current` → `bundle_id` via Control Plane (ou cache local)
3) Carrega bundle (ou cache) e executa pipeline determinístico
4) Aplica políticas runtime (ex.: rate limit)
5) Emite resposta e registra execução/auditoria

Saída:
- execução auditável: tenant + bundle_id + request_id + decisões

### 6.5 Rollback
1) Operador/CI solicita rollback do `current` para um bundle anterior
2) Control Plane valida permissões e aplica troca de alias
3) Auditoria registra rollback

Saída:
- produção volta ao bundle anterior sem “editar” artefatos


## 7. Contratos e fronteiras (interfaces)

### 7.1 Contrato de resolução de bundle
- Entrada: `tenant_id`, `alias`
- Saída: `bundle_id`, metadados e digest
- Requisitos:
  - baixa latência (cacheável)
  - consistente (alias deve resolver determinísticamente)

### 7.2 Contrato de execução
- Entrada:
  - identificação de tenant
  - payload de execução (ex.: question, conversation_id, etc. conforme bundle governado)
- Saída:
  - resposta do sistema governado
  - metadados mínimos (bundle_id, request_id, status)

### 7.3 Contrato de auditoria
- Eventos e campos mínimos padronizados
- Redaction/privacidade por policy (quando aplicável)


## 8. Multi-tenancy e isolamento (baseline)
Baseline (v1):
- Isolamento lógico por `tenant_id` em:
  - aliases
  - bundles visíveis
  - auditoria
  - limites operacionais
- Runtime deve impedir cross-tenant:
  - resolução de bundle só do tenant autenticado
  - logs/auditoria segregados por tenant (no mínimo por labels e separação lógica)

Evolução futura (não obrigatória na v1):
- runtime dedicado por tenant
- isolamento físico/namespace


## 9. Segurança (v1)
Requisitos mínimos:
- Autenticação e autorização para Control Plane (admin/ci)
- Autenticação para Runtime por tenant
- Assinatura/digest de bundle (integridade)
- Políticas para evitar execuções fora de `current`
- Rate limiting (policy-driven)
- Redaction de dados sensíveis em auditoria/logs (policy-driven)

Não objetivos nesta v1:
- KMS/rotacionamento avançado
- BYOK
- certificações (mas arquitetura deve permitir)


## 10. Observabilidade (v1)
No mínimo:
- Logs estruturados com `tenant_id`, `bundle_id`, `request_id/trace_id`
- Métricas de:
  - latência por rota e por tenant
  - taxa de sucesso/erro
  - rate-limit deny
  - cache hit/miss (se existir)
  - contagem de execuções por alias (`current`)
- Tracing distribuído (quando aplicável) com atributos padronizados

Requisito: sinais devem suportar diagnósticos e auditorias de incidentes.


## 11. Compatibilidade e evolução
- Bundles devem declarar compatibilidade com runtime (versão mínima ou contrato).
- Runtime deve rejeitar bundle incompatível (erro seguro).
- Mudanças breaking exigem ADR e plano de migração.
- Promoção é o mecanismo padrão de rollout; “hotfix” fora disso é fora de escopo.


## 12. Limites explícitos (v1)
O CONTRACTOR não é:
- plataforma de chatbot
- playground de prompts
- low-code de fluxos
- wrapper genérico de LLM
- sistema para experimentação sem governança
- local para armazenar dados de negócio do cliente
- mecanismo para alterações ad-hoc em produção sem trilha e promoção

Qualquer feature que viole governança, imutabilidade, determinismo ou separação CP/Runtime deve ser recusada por design.


## 13. Checklist de validação (arquitetura v1)
Para considerar este documento “em vigor”:
- [ ] ADR 0001 existe e referencia esta separação
- [ ] STATUS.md aponta a milestone atual corretamente
- [ ] ROADMAP.md tem fases técnicas antes de produto
- [ ] Definition of Done inclui atualização do STATUS.md
- [ ] Existe definição conceitual de bundle + aliases + promotion/rollback
