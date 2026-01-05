# ✅ Checklist — Stage 0 (Foundation)

Este checklist é **objetivo, verificável e não negociável**.
Stage 0 só termina quando **todos os itens** estiverem concluídos.

---

## 1. Repositório & Estrutura

* [ ] Repositório `contractor` criado
* [ ] Estrutura de pastas conforme arquitetura aprovada
* [ ] README.md fundacional presente
* [ ] `docs/FOUNDATION.md` com Guardrails v0
* [ ] `docs/ADR/` contendo ADRs 0001–0021
* [ ] Licença definida
* [ ] `.env.example` criado (sem segredos)

---

## 2. Guardrails & Governança

* [ ] ADRs versionados e imutáveis
* [ ] Processo de ADR documentado
* [ ] Política explícita de “no hardcode / no heuristics”
* [ ] Política de versionamento de bundles definida
* [ ] Papéis e responsabilidades documentados

---

## 3. Control Plane — Skeleton

* [ ] API sobe (healthz)
* [ ] Modelo de Tenant definido
* [ ] Modelo de Artifact/Bundle definido
* [ ] Registry local funcional (filesystem ou mock S3)
* [ ] Alias model (`draft`, `candidate`, `current`) implementado
* [ ] Audit log básico (append-only)

⚠️ Não é necessário UI no Stage 0.

---

## 4. Runtime — Skeleton

* [ ] API do runtime sobe (healthz)
* [ ] `TenantContext` implementado
* [ ] `ArtifactLoader` funcional (bundle local)
* [ ] Pipeline vazio mas encadeado:

  * planner (stub)
  * builder (stub)
  * executor (stub)
  * formatter (stub)
* [ ] Nenhuma lógica de domínio no código

---

## 5. Bundle Model (Formato)

* [ ] Estrutura de bundle definida e documentada
* [ ] `manifest.yaml` obrigatório e validado
* [ ] Exemplo de bundle mínimo funcional
* [ ] Bundle inclui:

  * ontology
  * entities
  * policies
  * templates
  * suites (mínimo)

---

## 6. Quality & Validation (mínimo)

* [ ] Validação estática de bundle (parse + schema)
* [ ] Smoke test de /ask com bundle mínimo
* [ ] Relatório de validação gerado
* [ ] Nenhuma promoção sem validação

---

## 7. Segurança Base

* [ ] Redaction layer obrigatória
* [ ] Nenhum segredo em código ou config
* [ ] Templates sandboxed (mesmo que stub)
* [ ] Logs sem dados sensíveis

---

## 8. Observabilidade Base

* [ ] Métricas básicas:

  * requests
  * errors
  * latency
* [ ] Labels tenant-aware (hash/alias)
* [ ] Logs estruturados
* [ ] Sem cardinalidade explosiva

---

## 9. Tenant Zero (Araquem)

* [ ] Araquem definido como tenant zero
* [ ] Bundle de referência separado
* [ ] Nenhuma dependência reversa (platform → Araquem)
* [ ] Smoke test roda com tenant Araquem

---

## 10. Critério de Saída do Stage 0

O Stage 0 está **concluído** quando:

* [ ] A plataforma sobe localmente (control + runtime)
* [ ] Um bundle mínimo é carregado
* [ ] Um `/ask` determinístico responde
* [ ] Nenhum hardcode de domínio existe
* [ ] ADRs governam todas as decisões estruturais
* [ ] O time consegue explicar o sistema **sem ambiguidade**

---

### 🚫 O que **não** fazer no Stage 0

* ❌ UI rica
* ❌ Conectores complexos
* ❌ Otimizações de performance
* ❌ Promessas comerciais
* ❌ Features enterprise

---
