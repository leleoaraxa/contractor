# Public Status Updates (Processo)

## Objetivo

Este runbook define o **processo** de atualização de status público com foco em:
- **Transparência** com clientes e stakeholders.
- **Redução de tickets** repetidos de suporte durante incidentes.
- **Governança** e consistência das mensagens públicas.

**Canal/ferramenta é fora de escopo** deste documento.

## Quando abrir status público

- **SEV-1:** obrigatório abrir status público.
- **SEV-2:** recomendado abrir status público.
- **SEV-3:** condicional, quando houver impacto amplo, comunicação prévia com clientes ou risco reputacional.
- **SEV-4:** geralmente não necessário.

## Conteúdo mínimo permitido

**Pode incluir (sanitizado e sem detalhes internos):**
- Identificador do incidente: <incident_id>.
- Resumo do impacto: <impact_summary>.
- Horário de início em UTC: <start_time_utc>.
- Status atual e mitigação em alto nível: <current_status>, <mitigation_summary>.
- Estimativa para próxima atualização: <next_update_eta>.

**Não pode incluir:**
- Payloads, dados sensíveis ou segredos.
- Detalhes internos de arquitetura, configuração ou vulnerabilidades.
- Logs, traces ou dados brutos de clientes.

## Cadência de updates

- Recomenda-se publicar updates em intervalos regulares (ex.: 60–120 minutos), ajustando
  conforme severidade e evolução do incidente.
- Evitar prometer disponibilidade 24x7; manter linguagem de recomendação e transparência.

## Encerramento

- Publicar mensagem de encerramento **sanitizada** com horário de fim (<end_time_utc>) e status final.
- Quando aplicável, incluir link para postmortem **sanitizado**.

## Fora de escopo

- Definição de ferramenta/canal específico para publicação.
- Integrações automáticas com sistemas externos.
