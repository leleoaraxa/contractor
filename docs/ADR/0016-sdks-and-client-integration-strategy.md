# 📘 ADR 0016 — **SDKs and Client Integration Strategy**

**Status:** Accepted
**Date:** 2026-01-05
**Canonical Name:**
**ADR 0016 — SDKs and Client Integration Strategy**

## Context

CONTRACTOR expõe APIs para:

* execução (/ask runtime)
* governança (control plane)
* automações (CI, quality, onboarding)

Clientes podem integrar via HTTP direto, mas SDKs:

* reduzem atrito de adoção
* padronizam boas práticas (auth, retries, timeouts)
* evitam uso incorreto da API
* aceleram time-to-value

Ao mesmo tempo, SDKs geram custo de manutenção e risco de acoplamento excessivo à API.

## Decision

Adotar uma estratégia **API-first**, com **SDKs thin, opinionated e opcionais**, alinhados estritamente aos contratos da API.

### Princípios

1. **API is the source of truth**
2. **SDKs are convenience layers, not platforms**
3. **No hidden logic in SDKs**

## Model

### API-First

* Todas as capacidades devem estar disponíveis via API HTTP documentada.
* OpenAPI é o contrato canônico.
* SDKs **não** introduzem endpoints ou comportamentos próprios.

### SDK Scope

SDKs devem oferecer apenas:

* autenticação e assinatura de requests
* retry/backoff padronizado
* timeouts seguros
* serialização/deserialização
* helpers de alto nível (ex.: `client.ask()`)

SDKs **não** devem:

* implementar lógica de negócio
* inferir parâmetros
* conter heurísticas
* mascarar erros da API

### SDK Roadmap

* MVP:

  * **Python SDK** (prioritário)
  * **JavaScript/TypeScript SDK**
* Fase posterior:

  * geração automática via OpenAPI (quando estável)
  * SDKs adicionais conforme demanda real

### Versioning

* SDK major version acompanha **API major version**.
* Breaking change de API ⇒ novo major do SDK.
* SDKs mantêm compatibilidade com APIs deprecated enquanto suportadas.

## Alternatives Considered

### 1) Sem SDKs (API only)

**Pros:** menos manutenção.
**Cons:** adoção mais lenta; maior erro de uso.

### 2) SDKs ricos com lógica própria

**Cons:** acoplamento alto; bugs difíceis; drift semântico.

### 3) **Thin SDKs, API-first (chosen)**

**Pros:** equilíbrio entre adoção e governança.

## Implications

* CI deve validar SDKs contra OpenAPI.
* Exemplos de uso em SDKs são parte da documentação oficial.
* SDKs devem ser tratados como produtos versionados (changelog, release notes).

## Consequences

Integração com CONTRACTOR torna-se **rápida, previsível e segura**, sem comprometer governança nem aumentar risco arquitetural.

---
