# CONTRACTOR

## One-liner

- CONTRACTOR é um control plane para sistemas de IA governados, que separa Control Plane e Runtime, permitindo empacotar, promover e operar pipelines de IA de forma auditável, determinística e segura em ambientes multi-tenant.

## Problema que resolve

- Quem sofre?
  Sofrem empresas e times que operam **IA em produção como parte crítica do produto ou da operação**, especialmente equipes de engenharia, dados e plataforma em ambientes B2B ou enterprise. São organizações que precisam de previsibilidade, responsabilidade e rastreabilidade, mas que hoje executam sistemas de IA sem uma base estrutural de governança. Para esses times, IA não é experimento — é infraestrutura — e qualquer falha impacta clientes, contratos, reputação e risco legal.

- Qual é a dor real?
  A dor real não está na escolha do modelo ou na qualidade da resposta isolada, mas na **falta de controle sobre o comportamento da IA em produção**. Sistemas se tornam não determinísticos, decisões não são reproduzíveis, mudanças ocorrem sem versionamento claro e incidentes são difíceis de diagnosticar ou reverter. Governança, auditoria e compliance acabam sendo tratados como camadas externas e frágeis, o que transforma a adoção de IA em um risco operacional crescente à medida que o sistema escala.

## O que É

- O CONTRACTOR é um control plane para execução governada de sistemas de IA que permite versionar, validar, promover e operar artefatos de IA de forma determinística e auditável, com separação explícita entre Control Plane e Runtime. Ele governa o comportamento da IA por meio de bundles imutáveis (ontologia, entidades, políticas, templates e suites), aplica políticas antes da execução, garante isolamento por tenant, oferece promoção e rollback controlados, impõe quality gates e fornece rastreabilidade completa das decisões em produção — tudo por design arquitetural, não por convenção ou processo manual.

## O que NÃO É

- O **CONTRACTOR** **não** é uma plataforma de chatbot, um playground de prompts, um construtor low-code de fluxos de IA nem um wrapper genérico de LLMs. Ele não serve para experimentação rápida sem governança, não executa lógica de domínio hardcoded, não armazena dados de negócio dos clientes, não toma decisões autônomas fora de contratos versionados e não permite mudanças diretas em produção sem promoção e rastreabilidade. Se o objetivo é velocidade sem controle, comportamento opaco ou customizações ad-hoc por código, o CONTRACTOR deliberadamente não atende esse escopo.


## Público-alvo
Segue a resposta organizada de forma **clara e objetiva**, cobrindo os dois pontos solicitados:

---

## Público-alvo

- **Quem usa:**
  O CONTRACTOR é utilizado principalmente por **times técnicos** que operam IA em produção — engenheiros de plataforma, engenharia de dados/IA, arquitetos de software e SREs — responsáveis por garantir execução determinística, governança, observabilidade e isolamento entre tenants. São equipes que tratam IA como **infraestrutura crítica**, não como experimento.

- **Quem paga:**
  Quem decide e paga pelo CONTRACTOR são **líderes técnicos e executivos** (CTOs, Heads of Engineering/Data/AI, responsáveis por plataforma e risco) e, em contextos enterprise, áreas de **compliance, segurança e produto**. O valor é percebido na redução de risco operacional, viabilização de contratos enterprise, previsibilidade de custos e capacidade de auditar e escalar IA com confiança.


## Métrica primária de sucesso

- A métrica primária de sucesso do **CONTRACTOR** é a **taxa de sistemas de IA operando em produção sob governança ativa**, medida pela proporção de execuções realizadas via bundles promovidos (`current`), passando por quality gates e com trilha de auditoria válida. Essa métrica reflete adoção real (uso em produção), retenção técnica (continuidade de uso sem bypass), eficiência operacional (menos incidentes e rollbacks manuais) e confiança institucional, indicando que a plataforma está sendo usada como **infraestrutura de execução**, não apenas como ferramenta auxiliar.

