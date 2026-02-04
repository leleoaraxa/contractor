# ADR 0008 — Compatibilidade e upgrade do Runtime

## Contexto
O CONTRACTOR separa explicitamente **bundles imutáveis** e **Runtime executável**.
À medida que o Runtime evolui, é necessário garantir que bundles existentes
continuem executáveis de forma segura ou sejam rejeitados de maneira explícita.

Sem regras formais de compatibilidade:
- bundles podem quebrar silenciosamente,
- upgrades de runtime tornam-se arriscados,
- rollback perde previsibilidade,
- governança se torna reativa.

Este ADR define **como compatibilidade é declarada, validada e aplicada**
entre bundles e Runtime.

## Opções consideradas
- Compatibilidade implícita baseada em “bom senso”
- Runtime tentando adaptar bundles antigos
- **Compatibilidade explícita, declarada e validada (v1)**

## Decisão
Adotar um modelo de **compatibilidade explícita e fail-closed**, onde:

- cada bundle **declara sua compatibilidade mínima com o Runtime**,
- o Control Plane **valida compatibilidade antes da promoção**,
- o Runtime **rejeita execução incompatível de forma explícita e auditada**.

Compatibilidade nunca é inferida.

## Declaração de compatibilidade

### No bundle
Todo bundle deve declarar, em `manifest.yaml`:

```yaml
runtime_compatibility:
  min_version: "1.0.0"
```

Opcionalmente (futuro):

* `max_version`
* `tested_versions`

## Versionamento do Runtime

O Runtime segue **Semantic Versioning (SemVer)**:

* **MAJOR**: mudanças breaking de contrato
* **MINOR**: novas capacidades backward-compatible
* **PATCH**: correções internas sem impacto de contrato

A versão do Runtime é exposta via:

* metadata interna
* auditoria
* (opcional) endpoint de status

## Validação no Control Plane

Durante gates de promoção (`candidate → current`):

* o Control Plane verifica se:

  * `runtime_compatibility.min_version <= runtime_alvo`
* bundles incompatíveis **não podem ser promovidos**.

Falha de compatibilidade:

* bloqueia promoção,
* gera evento de auditoria,
* exige novo bundle ou upgrade de runtime.

## Comportamento do Runtime

No momento da execução:

* o Runtime valida compatibilidade do bundle resolvido,
* se incompatível:

  * **não executa**,
  * retorna erro explícito,
  * registra auditoria,
  * não tenta fallback silencioso.

Esse comportamento é **fail-closed por design**.

## Estratégia de upgrade recomendada

1. Upgrade do Runtime (novo MAJOR/MINOR)
2. Validação de compatibilidade
3. Publicação de novos bundles
4. Promoção controlada (`candidate → current`)

Nunca o inverso.

## Breaking vs Non-breaking (exemplos)

### Mudanças breaking

* Alteração de schema de entidade obrigatória
* Remoção ou renomeação de policy obrigatória
* Mudança no contrato do endpoint `/execute`
* Alteração semântica de payload/resposta

### Mudanças non-breaking

* Nova policy opcional
* Novo intent/entidade
* Novo campo opcional em resposta
* Otimizações internas de execução

Mudanças breaking **exigem novo ADR e MAJOR bump**.

## Consequências

### Ganhos

* Upgrades previsíveis
* Produção protegida
* Auditoria clara de falhas
* Base sólida para CI e automação

### Custos

* Disciplina de versionamento
* Rejeição explícita em vez de “funcionar por acaso”

### Fora do escopo (v1)

* Compatibilidade automática entre majors
* Adaptação dinâmica de bundles antigos
* Migração automática de bundles
