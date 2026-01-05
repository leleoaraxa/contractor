
## ADR 0005 — Client Data Connectivity Model (Direct vs Agent)

**(Conexão direta vs Agent/Connector)**

**Status:** Accepted
**Data:** 2026-01-05
**Decisores:** SIRIOS / CONTRACTOR core team

### Contexto

O CONTRACTOR executa **compute-on-read** diretamente em fontes de dados do cliente. Isso levanta questões de:

* segurança (credenciais, superfície de ataque)
* conectividade (VPCs, firewalls, clouds distintas)
* latência e confiabilidade
* facilidade de onboarding no MVP
* requisitos enterprise futuros (compliance, zero-trust)

### Decisão

Adotar modelo **híbrido em fases**:

* **MVP / Default**: **conexão direta** do runtime ao banco do cliente
* **Enterprise / Evolução**: **Agent (Connector) opcional**, instalado no ambiente do cliente

A arquitetura e o código devem **desde o início** suportar ambos, via abstração.

### Alternativas consideradas

#### 1) Apenas conexão direta

**Prós**

* onboarding rápido
* menor complexidade inicial
* menos componentes para operar

**Contras**

* fricção de rede (firewall, IP allowlist, VPN)
* credenciais sensíveis no runtime
* difícil vender para enterprise
* problemas de compliance em ambientes restritos

#### 2) Apenas Agent desde o MVP

**Prós**

* segurança forte
* excelente para enterprise
* controle total de acesso local

**Contras**

* onboarding mais complexo
* alto custo de desenvolvimento inicial
* maior atrito comercial no early stage

#### 3) **Híbrido (decisão atual)**

**Prós**

* MVP rápido e funcional
* caminho claro para enterprise
* permite adaptar discurso comercial por segmento
* reduz retrabalho futuro se abstração for bem feita

**Contras**

* exige disciplina para não “colar” o runtime à conexão direta
* duas formas de operação para manter/testar

### Implicações práticas

#### Arquitetura

* Introduzir interface única no runtime:

  ```
  executor/db/base.py
    → execute(sql, params, context)
  ```
* Implementações:

  * `PostgresDirectExecutor`
  * `AgentExecutor` (fase futura)

#### Conexão direta (MVP)

* TLS obrigatório
* Credenciais armazenadas via Secrets Manager
* Permissões mínimas:

  * read-only
  * schemas explícitos
* Timeouts e rate limits obrigatórios
* Logs **nunca** incluem SQL com valores sensíveis

#### Agent (Enterprise)

* Container leve instalado na VPC do cliente
* Comunicação:

  * mTLS
  * outbound-only do agente (zero inbound no cliente)
* O agente:

  * executa SQL localmente
  * retorna apenas resultados
  * aplica allowlist de schemas/tables
* Runtime nunca recebe credenciais do banco do cliente

#### Políticas e contratos

* Cada datasource declara:

  * `connection_mode: direct | agent`
  * capacidades suportadas
* O Planner/Builder **não** sabe qual modo está sendo usado.

### Implicações de testes

* Testes de executor devem rodar:

  * com conexão direta mockada
  * com agent simulado (contract tests)
* Suites de qualidade não dependem do modo de conexão.

### Consequências (trade-off)

O MVP ganha velocidade sem comprometer o futuro enterprise. O custo é exigir **engenharia limpa desde o dia 1** para manter a abstração correta.

---

## Encerramento (alinhamento estratégico)

Com os ADRs **0001–0005**, o CONTRACTOR já tem decisões críticas tomadas sobre:

* separação de responsabilidades
* versionamento e rollback
* isolamento multi-tenant
* storage de artefatos
* acesso a dados do cliente

Isso reduz drasticamente o risco de **refatoração estrutural** quando:

* AWS stage escalar
* primeiros clientes externos entrarem
* exigências enterprise surgirem
