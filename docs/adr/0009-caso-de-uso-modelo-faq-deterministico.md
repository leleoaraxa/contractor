# ADR 0009 — Caso de uso modelo (Demo: FAQ determinístico com JSON/SQLite)

## Contexto
O CONTRACTOR possui agora todos os contratos estruturais definidos
(Control Plane, Runtime, bundles, compatibilidade e governança).
Para validar o pipeline end-to-end e servir como referência didática
para futuros usuários e contribuidores, é necessário definir um
**caso de uso modelo** simples, determinístico e de fácil compreensão.

Este caso de uso deve:
- exercitar todo o fluxo governado (bundle → gates → promoção → execução),
- não depender de infraestrutura pesada,
- ser reproduzível em ambiente local e CI,
- ser compreensível por quem não conhece o domínio do CONTRACTOR.

## Opções consideradas
- Demo complexa com banco relacional enterprise
- Demo puramente “echo” sem significado funcional
- **Demo determinística de FAQ com dados estáticos (JSON/SQLite)**

## Decisão
Adotar como **caso de uso modelo oficial do CONTRACTOR** uma
**Demo de FAQ determinístico**, onde:

- o comportamento é governado por bundle,
- os dados de FAQ são lidos de arquivos JSON ou SQLite local,
- o Runtime executa apenas leitura determinística,
- todo o pipeline do CONTRACTOR é exercitado sem dependências externas.

Este caso de uso é **didático**, **não opinativo** e **não representa
o escopo final do produto**, servindo exclusivamente como referência
técnica e base de testes.

## Descrição do caso de uso

### Visão geral
O sistema responde perguntas de FAQ previamente definidas, retornando
respostas determinísticas a partir de dados estáticos versionados
no bundle.

Exemplo de pergunta:
> “Como funciona a promoção de bundles no CONTRACTOR?”

Resposta:
> Texto previamente definido no dataset de FAQ.

Não há inferência probabilística, aprendizado ou escrita de dados.

---

## Arquitetura do caso de uso

### Bundle (demo)
O bundle de demo deve conter, no mínimo:

```

bundle/
├── manifest.yaml
├── ontology/
│   └── ontology.yaml          # intent faq_query
├── entities/
│   └── faq_answer.schema.yaml # contrato da resposta
├── data/
│   ├── faq.json               # dataset principal (obrigatório)
│   └── faq.db                 # SQLite opcional (demo avançada)
├── policies/
│   └── security.yaml
├── templates/
│   └── faq_answer.j2
├── suites/
│   └── faq_golden.json        # perguntas → respostas esperadas
└── metadata/
└── bundle.yaml

```

### Fonte de dados
- **Primária (obrigatória):** `data/faq.json`
- **Opcional (demo estendida):** `data/faq.db` (SQLite)

Regras:
- SQLite é **apenas um adapter de demo**, não um contrato do Runtime.
- O Runtime pode alternar entre JSON ou SQLite por configuração local,
  sem alterar ADRs ou contratos.
- Dados são **somente leitura**.

---

## Comportamento do Runtime (demo)

### Execução
- Endpoint: `POST /execute`
- Fluxo:
  1. Autentica tenant
  2. Resolve alias `current` via Control Plane
  3. Carrega bundle aprovado
  4. Identifica intent `faq_query`
  5. Consulta FAQ via JSON ou SQLite
  6. Valida resposta contra schema
  7. Retorna resposta + metadados
  8. Emite auditoria de execução

### Metadados mínimos retornados
- `request_id`
- `bundle_id`
- `tenant_id`
- `intent`
- status da execução

---

## Quality gates (demo)

O bundle de FAQ deve passar por gates que validem:
- estrutura mínima do bundle (ADR 0005),
- validade da ontologia,
- validade dos schemas,
- execução das **suites golden**:
  - perguntas conhecidas retornam respostas exatas,
  - qualquer divergência falha o gate.

Esse gate garante **determinismo verificável**.

---

## Papel do Control Plane
No caso de uso modelo, o Control Plane:
- publica o bundle de FAQ,
- executa gates,
- promove `candidate → current`,
- resolve alias para o Runtime,
- registra auditoria de todas as ações.

Nenhum atalho é permitido para a demo.

---

## O que este caso de uso DEMONSTRA
- Governança por bundle
- Execução determinística
- Separação Control Plane / Runtime
- Promoção e rollback
- Auditoria end-to-end
- Compatibilidade e versionamento
- Pipeline validável em CI/local

## O que este caso de uso NÃO É
- Não é recomendação de arquitetura de dados
- Não é benchmark de performance
- Não é exemplo de IA generativa
- Não é modelo de produto final

---

## Consequências

### Ganhos
- Caso de referência simples e universal
- Base sólida para testes de integração
- Onboarding técnico facilitado
- Demonstração clara do valor do CONTRACTOR

### Custos
- Manutenção de um bundle de demo
- Código de adapter (JSON/SQLite) específico para demo

### Fora do escopo
- Escrita de dados
- Atualização dinâmica de FAQ
- Interface gráfica
- Multi-idioma

## Status
- Aprovado como **caso de uso modelo oficial do CONTRACTOR**
- Deve ser usado como referência para demos, testes e documentação
