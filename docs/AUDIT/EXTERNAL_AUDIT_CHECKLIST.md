## 🛡️ CONTRACTOR — External Audit Readiness Checklist

Este checklist organiza evidências mínimas esperadas por auditorias **SOC 2 / ISO 27001-style**, sem prometer certificações.

---

## 🔐 Segurança & Acesso

* [ ] Modelo de threat definido (ADR 0007)
* [ ] Separação clara Control/Data Plane
* [ ] API Keys nunca persistidas
* [ ] IAM documentado por estágio (ADR 0027)

---

## 🧾 Governança & Mudança

* [ ] ADRs versionados e imutáveis
* [ ] Processo formal de mudança (ADR 0020)
* [ ] Promotion gates auditáveis
* [ ] Rollback documentado

---

## 📊 Observabilidade & SLOs

* [ ] SLOs ativos e mensuráveis
* [ ] Alertas documentados
* [ ] Incident Management formal
* [ ] Postmortems registrados

---

## 🔏 Privacidade & Dados

* [ ] Classificação de dados (ADR 0018)
* [ ] Política de retenção documentada
* [ ] Zero retention para dados de domínio
* [ ] Evidência de purge manual

---

## 🧪 Qualidade & Confiabilidade

* [ ] Quality gates automatizados
* [ ] Suites versionadas
* [ ] Histórico de promotion/rollback
* [ ] SDKs versionados

---

## 📁 Evidências Esperadas

* ADRs (docs/ADR)
* Runbooks (docs/RUNBOOKS)
* Status & readiness docs
* Logs/audit logs
* Métricas SLO

---

> **Nota:** CONTRACTOR é *audit-ready*, não *audit-certified* por padrão.

---
