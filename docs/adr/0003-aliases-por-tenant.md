# ADR 0003 — Modelo de aliases por tenant (draft / candidate / current)

## Contexto
Para operar IA como infraestrutura crítica, é necessário separar:
- criação e validação de bundles
- execução em produção

Um mecanismo de promoção explícita é essencial para garantir previsibilidade,
controle e rollback sem mutação de artefatos.

## Opções consideradas
- Execução direta por bundle_id
- Flags manuais em runtime
- Aliases de promoção por tenant

## Decisão
O CONTRACTOR adota um modelo de **aliases por tenant**, onde cada tenant possui
os seguintes ponteiros lógicos:

- `draft`: bundle em desenvolvimento/teste
- `candidate`: bundle aprovado em gates, pronto para produção
- `current`: bundle ativo em produção

Aliases **não alteram o bundle**, apenas apontam para um `bundle_id` imutável.

## Consequências
**Ganhos**
- Promoção e rollback seguros (troca de ponteiro)
- Isolamento por tenant
- Possibilidade de múltiplos ciclos de validação
- Clareza operacional (estado explícito)

**Custos**
- Necessidade de gerenciar estado adicional (aliases)
- Operação levemente mais complexa

**Regras explícitas**
- Runtime só pode executar alias `current`
- Alteração de alias exige auditoria
- Um tenant pode ter bundles diferentes de outro tenant

**Fora do escopo**
- Execução direta de `draft` ou `candidate` em produção
- Alias global compartilhado entre tenants
