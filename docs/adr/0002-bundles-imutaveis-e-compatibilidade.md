# ADR 0002 — Bundles imutáveis, identificação e compatibilidade

## Contexto
O CONTRACTOR governa o comportamento de sistemas de IA por meio de bundles.
Para garantir determinismo, auditabilidade e rollback seguro, é necessário impedir
qualquer mutação implícita ou alteração direta de artefatos em produção.

Sem imutabilidade:
- mudanças não são rastreáveis,
- execuções não são reproduzíveis,
- rollback se torna incerto,
- auditoria perde valor operacional.

## Opções consideradas
- Bundles mutáveis com versionamento lógico
- Bundles imutáveis identificados por versão/hash

## Decisão
Bundles no CONTRACTOR são **imutáveis por design**.

Cada bundle é identificado por um `bundle_id` único e imutável, derivado de:
- versão lógica (ex.: timestamp ou semver)
- digest/hash do conteúdo

Além disso, cada bundle **declara explicitamente sua compatibilidade** com o runtime
(ex.: versão mínima suportada).

## Consequências
**Ganhos**
- Execuções totalmente reproduzíveis
- Auditoria confiável
- Rollback seguro via troca de alias
- Detecção precoce de incompatibilidade

**Custos**
- Mais disciplina no fluxo de publicação
- Necessidade de criar novo bundle para qualquer alteração

**Fora do escopo**
- Edição direta de bundles em produção
- “Hotfix” sem novo bundle
