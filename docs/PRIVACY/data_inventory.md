# Inventário de dados (Stage 2) — ADR 0021

> Referência: ADR 0021 — Product roadmap e maturity stages.

Este inventário descreve o **mínimo necessário** para o Stage 2 (Production Ready) e não implica requisitos enterprise.

## 1) Dados de entrada do usuário

| Dado | Onde aparece | Persistência | Risco |
| --- | --- | --- | --- |
| `question` | Payload do `/api/v1/runtime/ask` (AskRequest). | Pode entrar em cache (payload canônico/resultado) e em respostas do runtime; não persistimos fora disso. | Médio (conteúdo pode conter PII; não deve ser logado em plaintext). |
| `tenant_id` | Payload do `/api/v1/runtime/ask` (AskRequest), usado em cache key e contexto. | Cache (chave) e resposta (`meta`). | Baixo (identificador lógico). |
| `bundle_id` / `release_alias` | Payload do `/api/v1/runtime/ask` (AskRequest) e resolução de bundle. | Cache (chave/metadata) e resposta (`meta`). | Baixo (identificador de artefato). |
| Headers (`X-API-Key`) | Header de autenticação em runtime/control. | **Não** é persistido; apenas validado. | Alto (credencial). |

## 2) Dados derivados

| Dado | Onde aparece | Persistência | Risco |
| --- | --- | --- | --- |
| Plano/decisões do planner | Pipeline `/ask` (plan/decision) e `meta` da resposta. | Cache do runtime pode persistir `plan`/`decision` junto do resultado. | Médio (pode refletir intenção do usuário). |
| Erros estruturados | `detail` de HTTPException no runtime/control. | Resposta ao cliente e logs de aplicação. | Baixo/Médio (sem payload sensível). |

## 3) Telemetria

| Dado | Onde aparece | Persistência | Risco |
| --- | --- | --- | --- |
| Logs de aplicação | JSON logger padrão (stdout). | Retenção depende do ambiente (container/log driver). | Médio (risco se payload sensível for logado). |
| Métricas Prometheus | Métricas de worker async (Prometheus client). | Prometheus (retention configurável). | Baixo (não contém payload). |
| Traces | Não implementados no runtime atual. | N/A | Baixo (não aplicável). |

## 4) Artefatos e bundles

| Dado | Onde aparece | Persistência | Risco |
| --- | --- | --- | --- |
| Registry (ontologia/policies/templates/suites) | `registry/` e manifest do bundle. | Persistência em filesystem (imutável por bundle). | Baixo (artefatos versionados). |

## Notas

- Logs passam por redaction básica; não há detecção automática de PII. A política proíbe registrar dados sensíveis em logs. 
- O cache do runtime pode conter `question` em plaintext (payload canônico e resposta); por padrão é efêmero e com TTL configurável.
