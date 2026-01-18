# NEXT STEPS — CONTRACTOR (Roadmap para Stage 3 Enterprise Ready)

Este plano foca em fechar os gaps identificados para declarar o **Stage 3 (Enterprise Ready)** como completo e auditável.

## 1. O que falta para Stage 3 (Enterprise Ready)

- **Validação de Produção:** Evidência real de rollback e operação enterprise.
- **Sincronização de Contratos:** Unificar Schemas YAML com o código de validação.
- **Observabilidade:** Métricas de tenant em modo pool (compartilhado).
- **Consistência Documental:** Corrigir duplicidades e relatórios defasados.

---

## 2. Sequência Recomendada (Passo a Passo)

### Passo 1: Unificação da Validação de Contratos
- **Objetivo:** Garantir que os Schemas YAML em `contracts/` sejam a única fonte de verdade.
- **Arquivos:** `app/control_plane/domain/bundles/contracts_validator.py`.
- **Critério de Aceite:** Substituir validação manual por `jsonschema.validate()` usando os arquivos em `contracts/`.
- **Teste:** Rodar `tests/integration/test_bundle_contract_validation.py` com payloads que violem regex do schema.

### Passo 2: Atualização do Relatório de Auditoria Stage 3
- **Objetivo:** Refletir o estado real das evidências (dashboards e ADRs).
- **Arquivos:** `docs/ADR/STAGE_3_READINESS_AUDIT.md`.
- **Critério de Aceite:** Marcar dashboards como ✅ e ADRs como ✅.
- **Teste:** Revisão visual do arquivo MD.

### Passo 3: Extensão de Métricas de Tenant para Modo Pool
- **Objetivo:** Ter visibilidade por tenant mesmo quando o runtime não é dedicado.
- **Arquivos:** `app/runtime/api/metrics.py`.
- **Critério de Aceite:** `record_tenant_request` deve registrar métricas mesmo se `dedicated_tenant_id` for nulo, usando o `tenant_id` do request.
- **Teste:** `tests/integration/test_runtime_tenant_observability.py` em modo compartilhado.

### Passo 4: Unificação dos Documentos Executivos
- **Objetivo:** Eliminar confusão de idioma e conteúdo.
- **Arquivos:** `docs/EXECUTIVE-OVERVIEW.md`, `docs/EXECUTIVE/EXECUTIVE_OVERVIEW.md`.
- **Critério de Aceite:** Manter apenas a versão em `docs/EXECUTIVE/` (preferencialmente em EN como padrão enterprise, com tradução PT opcional).

### Passo 5: Implementação de Retenção por Tenant
- **Objetivo:** Atender requisitos de compliance enterprise (ADR 0018).
- **Arquivos:** `ops/observability/retention.yaml`, novo módulo `app/shared/config/retention.py`.
- **Critério de Aceite:** Permitir que o Control Plane leia políticas de retenção específicas do bundle do tenant.

### Passo 6: Evidência de Rollback em "Quase-Produção"
- **Objetivo:** Mitigar falta de produção real.
- **Arquivos:** `docs/EVIDENCE/stage_3/rollback_staging_validation.md`.
- **Critério de Aceite:** Executar `scripts/quality/smoke_quality_gate.py` em ambiente de staging (não-local) e documentar o log de saída.

---

## 3. Fora do Roadmap (Não fazer agora)

- **Marketplace Automação (Stage 4):** Não iniciar implementação de faturamento de marketplace.
- **Autoscaling Inteligente:** Manter escalonamento manual/estático por enquanto.
- **Multi-região Ativa:** O suporte atual é apenas de Data Residency (isolamento), não failover global.
