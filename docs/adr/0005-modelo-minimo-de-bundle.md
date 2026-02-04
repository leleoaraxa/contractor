# ADR 0005 — Modelo mínimo de bundle

## Contexto
O CONTRACTOR governa sistemas de IA por meio de **bundles imutáveis**, que encapsulam
todo o comportamento permitido em produção. Para garantir determinismo,
auditabilidade, compatibilidade e evolução segura, é necessário definir um
**modelo mínimo de bundle** — isto é, quais artefatos são obrigatórios, como são
organizados e quais metadados devem existir.

Sem um modelo mínimo explícito:
- bundles tornam-se inconsistentes entre si,
- quality gates ficam frágeis ou incompletos,
- compatibilidade com o runtime é ambígua,
- auditoria perde capacidade de correlação.

Este ADR define o **baseline v1** do bundle, suficiente para execução governada em
produção, sem introduzir escopo de produto, UX ou domínio específico.

## Opções consideradas
- Bundle flexível sem layout fixo (conteúdo ad-hoc)
- Bundle totalmente prescritivo e extenso (overhead alto)
- **Bundle mínimo prescritivo com extensibilidade controlada** (baseline v1)

## Decisão
Adotar um **modelo mínimo de bundle prescritivo**, com:
- **layout de diretórios padronizado**,
- **artefatos obrigatórios**,
- **metadados explícitos** de compatibilidade e identidade,
- **extensibilidade controlada** para futuras evoluções.

Qualquer bundle que não cumpra este modelo **não é válido** e deve falhar nos gates.

## Estrutura mínima do bundle (v1)

```

bundle/
├── manifest.yaml
├── ontology/
│   └── ontology.yaml
├── entities/
│   └── *.schema.yaml
├── policies/
│   └── *.yaml
├── templates/
│   └── *.j2
├── suites/
│   └── *.json
└── metadata/
   └── bundle.yaml

```

### Descrição dos componentes obrigatórios

#### 1) `manifest.yaml`
Arquivo raiz que identifica e descreve o bundle.

Campos mínimos:
- `bundle_name`
- `bundle_version` (lógica)
- `bundle_id` (imutável, calculado pelo Control Plane)
- `created_at`
- `created_by`
- `runtime_compatibility` (ex.: versão mínima do runtime)
- `description` (curta)

Função:
- Ponto único de identificação do bundle
- Base para auditoria e validação inicial

#### 2) `ontology/`
Contém a ontologia que governa:
- termos válidos,
- intenções,
- entidades conceituais.

Regras:
- Deve existir exatamente um `ontology.yaml`
- Ontologia governa roteamento e interpretação
- Runtime não executa lógica fora da ontologia declarada

#### 3) `entities/`
Define os **contratos de dados** utilizados pelo sistema governado.

Regras:
- Cada entidade deve possuir schema explícito (`*.schema.yaml`)
- Schemas são a fonte de verdade para validação de payloads e respostas
- Runtime deve rejeitar execuções que violem schemas

#### 4) `policies/`
Define políticas governadas, como:
- segurança,
- cache,
- rate limiting,
- RAG (quando aplicável),
- redaction.

Regras:
- Políticas são declarativas
- Ausência de política obrigatória deve falhar gate
- Runtime apenas **aplica** políticas; não decide políticas

#### 5) `templates/`
Templates de saída e/ou narrativas governadas.

Regras:
- Templates são declarativos
- Não podem conter lógica de domínio fora do escopo permitido
- Templates perigosos ou não determinísticos devem falhar gate

#### 6) `suites/`
Suites de qualidade e validação.

Exemplos:
- routing suites
- threshold suites
- golden tests

Regras:
- Pelo menos uma suite deve existir
- Suites são executadas no Control Plane
- Resultados são auditados e versionados

#### 7) `metadata/bundle.yaml`
Metadados adicionais e extensíveis do bundle.

Campos mínimos:
- `owner`
- `tags`
- `environment` (ex.: prod, staging)
- `notes` (livre)

Função:
- Informação operacional e organizacional
- Não afeta execução direta do runtime

## Regras de validação (quality gates)
Um bundle só pode ser promovido se:
- layout estiver conforme o modelo mínimo,
- todos os artefatos obrigatórios existirem,
- schemas e ontologia forem válidos,
- policies obrigatórias estiverem presentes,
- suites executarem sem falhas,
- compatibilidade com runtime for atendida.

Falha em qualquer regra bloqueia promoção para `candidate` ou `current`.

## Consequências

### Ganhos
- Determinismo e previsibilidade
- Bundles comparáveis e auditáveis
- Gates mais fortes e automatizáveis
- Base sólida para evolução futura
- Redução de erro humano e ad-hoc

### Custos
- Maior disciplina na criação de bundles
- Overhead inicial de estrutura mínima

### Fora do escopo (v1)
- Customização de layout por tenant
- Execução parcial de bundle
- Alteração dinâmica de artefatos em produção
- UI para edição de bundles

## Evolução futura
O modelo mínimo poderá evoluir via novos ADRs para:
- extensões opcionais,
- múltiplas ontologias por bundle,
- bundles compostos,
- compatibilidade multi-runtime.

Qualquer mudança no modelo mínimo **exige novo ADR**.

## Status
- Válido a partir da arquitetura v1
- Obrigatório para todos os bundles do CONTRACTOR
