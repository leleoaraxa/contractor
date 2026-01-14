# Stage 3 — Estratégia de Isolamento de Recursos do Runtime (CPU, Memória, Cache)

## 1. Context & Requirement

O item **1.2 do ADR 0028** exige **isolamento de recursos (CPU, memória, cache)** para declarar o Stage 3 como Enterprise Ready. Esse isolamento é **obrigatório**, **infra-level** (não apenas lógico) e precisa ser **auditável no repositório**. O modelo de runtime dedicado está definido no ADR 0022 e o checklist do ADR 0028 não pode ser encerrado sem evidências explícitas de limites e segregação por runtime dedicado. **Stage 3 ≠ Stage 4**: o objetivo é um isolamento mínimo, previsível e defensável, sem avançar para automações avançadas ou multi-cluster. O estado atual de `docker-compose.yml` e o relatório de evidências apontam ausência de limites explícitos e cache compartilhado, logo o requisito ainda está **aberto** até implementação e evidência.

## 2. Threat Model resumido (Stage 3)

**Riscos relevantes (Stage 3):**

* **Noisy neighbor:** um runtime dedicado pode degradar outro se não houver limites de CPU/memória por instância.
* **Resource starvation:** ausência de limites permite consumo total de CPU/memória, degradando disponibilidade e SLOs.
* **Cache bleed:** cache compartilhado entre runtimes/tenants aumenta risco de vazamento ou contaminação lógica de estado.
* **Impacto cruzado em incidentes:** falhas de um runtime podem afetar outros por ausência de isolamento físico/infra.

## 3. Opções de Implementação Avaliadas

### Opção A — Docker / Compose (mínimo viável Stage 3)

**CPU**
* Configurar limites explícitos por runtime dedicado (ex.: `cpus`, `cpu_quota` ou `deploy.resources.limits.cpus` quando suportado).

**Memória**
* Definir limites por runtime dedicado (`mem_limit` ou `deploy.resources.limits.memory`).
* Documentar comportamento em caso de OOM (ex.: restart policy e impacto esperado no runtime dedicado).

**Cache**
* **Isolar cache por runtime dedicado** de forma auditável:
  * Redis dedicado por runtime, ou
  * DB/namespace isolado com chaveamento explícito por tenant/runtime.

**Observações de Stage 3**
* Mantém operação simples e aderente ao desenho de runtime dedicado do ADR 0022.
* Não exige mudanças em orchestration avançada.
* Permite evidência clara via arquivos de configuração versionados (ex.: `docker-compose.yml`).

### Opção B — Kubernetes (baseline enterprise)

**Requests / Limits**
* Definir `requests` e `limits` por runtime dedicado para CPU/memória.

**Namespaces**
* Segregar runtime dedicado por namespace ou por deployment isolado.

**Network / Resource isolation**
* Usar NetworkPolicies e quotas de recursos (ResourceQuota/LimitRange).

**Custo operacional adicional**
* Exige stack de cluster, observabilidade e governança de namespaces.
* Maior complexidade operacional para Stage 3 (não obrigatório).

## 4. Tabela de Trade-offs (obrigatória)

| Critério | Docker (Compose) | Kubernetes | Impacto no Stage 3 | Motivo de aceitação ou rejeição |
| --- | --- | --- | --- | --- |
| Limites de CPU | Suportado via parâmetros de container (ex.: `cpus`, `cpu_quota`). | Suportado via `requests/limits`. | Ambos atendem item 1.2. | **Aceito (Docker)** por ser mínimo viável e auditável. |
| Limites de memória | Suportado via `mem_limit`/`deploy.resources.limits.memory`. | Suportado via `requests/limits`. | Ambos atendem item 1.2. | **Aceito (Docker)** por simplicidade operacional. |
| Isolamento de cache | Redis dedicado por runtime ou namespace por tenant. | Redis dedicado por namespace ou deployment isolado. | Necessário para mitigar cache bleed. | **Aceito (Docker)** se houver segregação clara e evidência no repo. |
| Auditoria e evidência | Arquivos versionados (compose/infra). | Manifests versionados. | Ambos permitem auditoria. | **Aceito (Docker)** se houver versionamento explícito. |
| Complexidade operacional | Baixa. | Alta (cluster, RBAC, policies). | Stage 3 não exige escalas avançadas. | **Rejeitado (K8s)** como requisito mínimo; opcional. |

## 5. Definição do “Mínimo Aceitável para Stage 3”

**CPU**
* **Obrigatório:** limites explícitos por runtime dedicado (por container/serviço) em configuração de infra versionada.
* **Onde:** configuração de runtime dedicado (ex.: `docker-compose.yml` ou equivalente de provisionamento).

**Memória**
* **Obrigatório:** limite explícito de memória por runtime dedicado e comportamento OOM documentado.
* **Onde:** configuração de runtime dedicado (compose/k8s) + nota operacional sobre comportamento em OOM.

**Cache**
* **Obrigatório:** isolamento físico ou lógico do cache por runtime dedicado.
* **Onde:** configuração do runtime indicando Redis exclusivo ou namespace/chaveamento inequívoco por tenant/runtime.

**O que NÃO é exigido ainda (Stage 4)**
* Autoscaling horizontal ou inteligente.
* Fairness algorítmica entre tenants.
* Billing por consumo.
* Multi-cluster ou orquestração avançada.

## 6. Critério de Fechamento do Checklist (ADR 0028)

Checklist auditável para mover o item **1.2** de ❌ → ✅ quando implementado:

* [ ] Runtime dedicado possui limites de **CPU** configurados em infra versionada.
* [ ] Runtime dedicado possui limites de **memória** configurados em infra versionada.
* [ ] Comportamento de **OOM** é conhecido e documentado (runbook ou nota operacional).
* [ ] **Cache não é compartilhado** entre runtimes dedicados (Redis dedicado ou namespace isolado).
* [ ] Evidência registrada em `docs/EVIDENCE/stage_3/runtime_resource_isolation.md` com referência à configuração real.

## 7. Explicit Non-Goals (Stage 4 boundary)

* Autoscaling horizontal.
* Fairness entre tenants.
* Billing por consumo.
* Marketplace de infra/abstrações de runtime.
* Multi-cluster ou orquestração avançada.
