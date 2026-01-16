# Customer Communication Templates (Sanitized)

Este documento fornece templates **sanitizados** e **sem detalhes internos** para comunicação com clientes em incidentes.
Os textos são neutros, sem dados internos, sem payloads e sem segredos. O canal de envio é **fora de escopo**.

## Template — Initial notice (SEV-1 / SEV-2)

**Assunto:** [Incidente] <incident_id> — Impacto identificado

**Mensagem (sanitized):**

> Olá,
> 
> Identificamos um incidente que pode impactar o serviço. Esta mensagem é **sanitizada** e **sem detalhes internos**.
> 
> **Resumo do impacto:** <impact_summary>
> **Início (UTC):** <start_time_utc>
> **Severidade:** <severity>
> **Status atual:** <current_status>
> 
> Estamos trabalhando para mitigar o impacto. Compartilharemos atualizações conforme houver progresso.
> 
> **Próxima atualização estimada:** <next_update_eta>
> 
> Obrigado pela compreensão.

## Template — Progress update

**Assunto:** [Incidente] <incident_id> — Atualização de progresso

**Mensagem (sanitized):**

> Olá,
> 
> Segue atualização **sanitizada** e **sem detalhes internos** sobre o incidente.
> 
> **Resumo do impacto:** <impact_summary>
> **Status atual:** <current_status>
> **Mitigação em andamento:** <mitigation_summary>
> **Estimativa para próxima atualização:** <next_update_eta>
> 
> Recomendação de cadência: enviar updates em intervalos regulares (ex.: a cada 60–120 minutos),
> ajustando conforme severidade e evolução do incidente.
> 
> Obrigado pela compreensão.

## Template — Resolution notice

**Assunto:** [Incidente] <incident_id> — Encerramento

**Mensagem (sanitized):**

> Olá,
> 
> O incidente foi resolvido. Esta mensagem é **sanitizada** e **sem detalhes internos**.
> 
> **Resumo do impacto:** <impact_summary>
> **Início (UTC):** <start_time_utc>
> **Fim (UTC):** <end_time_utc>
> **Status final:** <final_status>
> 
> Quando aplicável, compartilharemos um postmortem **sanitizado**.
> 
> Obrigado pela compreensão.
