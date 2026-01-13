## 📊 CONTRACTOR — Readiness Checklist by Maturity Stage

Este documento define **critérios objetivos e auditáveis** para progressão entre estágios do CONTRACTOR, conforme ADR 0021.

---

## 🟡 Stage 0 — Foundation (Non-Commercial)

**Arquitetura**

* [ ] Runtime funcional
* [ ] Control Plane funcional
* [ ] Separação clara Control/Data Plane (ADR 0001)

**Artefatos**

* [ ] Bundles imutáveis
* [ ] Versionamento funcional
* [ ] Registry operacional

**Governança**

* [ ] ADRs 0001–0009 definidos

❌ **Não comercializável**

---

## 🟠 Stage 1 — MVP (Early Adopters)

**Operação**

* [ ] Multi-tenant pool funcional
* [ ] Cache e rate limiting ativos
* [ ] Billing interno (metering)

**Observabilidade**

* [ ] Logs estruturados
* [ ] Métricas básicas

**Governança**

* [ ] ADRs até 0017 aceitos

⚠️ **Comercial restrito (design partners)**

---

## 🟢 Stage 2 — Production Ready

**Confiabilidade**

* [ ] SLOs ativos (ADR 0019 / 0021)
* [ ] Incident Management documentado
* [ ] Rollback completo funcional

**Governança**

* [ ] Políticas de privacidade e retenção (ADR 0018)
* [ ] Change management ativo (ADR 0020)

**Produto**

* [ ] SDKs estáveis
* [ ] Contratos de API versionados

✅ **Comercial geral (SMB / Pro)**

---

## 🔵 Stage 3 — Enterprise Ready

**Isolamento**

* [ ] Runtime dedicado por tenant (ADR 0022)
* [ ] Isolamento forte de recursos

**Contratos**

* [ ] SLA formalizado (ADR 0023)
* [ ] Escalonamento enterprise (ADR 0025)

**Compliance**

* [ ] Data residency definida (ADR 0026)
* [ ] IAM avançado (ADR 0027)
* [ ] Observabilidade por tenant (ADR 0024)

**Governança**

* [ ] Checklist Stage 3 completo (ADR 0028)

✅ **Enterprise Ready**

---

## 🟣 Stage 4 — Platform Ecosystem

**Marketplace**

* [ ] Governança de bundles (ADR 0030)
* [ ] Lifecycle de parceiros (ADR 0031)
* [ ] Modelo comercial e billing (ADR 0032–0033)

**Confiança**

* [ ] Reputação e rating (ADR 0036)
* [ ] Enforcement de qualidade (ADR 0037)

**Sustentabilidade**

* [ ] Exit & sunset model definido (ADR 0038)

🚀 **Plataforma & Ecossistema**

---

## 🔒 Regra de Ouro

> **Nenhum estágio é declarado sem checklist completo.**
> Marketing, vendas e contratos **devem referenciar este documento**.

---
