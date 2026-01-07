# FOUNDATION HARDENING PACK — Stage 0

## Escopo executado
- Adicionado LICENSE (MIT) na raiz.
- Criado `.env.example` alinhado com `app/shared/config/settings.py` e `docker-compose.yml`.
- Completados `docs/C4/context.md` e `docs/C4/container.md` com diagramas e descrições do Control Plane, Runtime, registry filesystem e placeholder Redis.
- Criados runbooks em `docs/RUNBOOKS/` (`run_local`, `run_docker`, `release_promotion`, `troubleshooting`).
- Adicionados scripts Linux em `scripts/dev/` (`run_control.sh`, `run_runtime.sh`, `run_all.sh`, `smoke.sh`) preservando os scripts Windows existentes.
- Padronizado `Makefile` com alvos `dev`, `docker-up`, `smoke`, `lint`, `fmt`.
- Atualizado `README.md` com “How to run” e “Stage 0 Exit Criteria”.

## Mapeamento para CHECKLIST-STAGE-0
- **1. Repositório & Estrutura**
  - Licença definida: **DONE** (LICENSE MIT).
  - `.env.example` criado (sem segredos): **DONE**.
  - README fundacional + referências atualizadas: **DONE**.
  - Estrutura de docs C4/context/container preenchida: **DONE**.
- **2. Guardrails & Governança**
  - ADRs permanecem imutáveis; documentação reforçada via C4 e runbooks (sem mudanças em ADRs): **UNCHANGED** (conforme escopo).
- **3. Control Plane — Skeleton**
  - Registry local filesystem documentado e scripts para subir/validar: **PARTIAL (docs/scripts)**; implementação já existia.
- **4. Runtime — Skeleton**
  - Execução /ask documentada e smoke test script: **PARTIAL (docs/scripts)**; código base já existente.
- **5. Bundle Model (Formato)**
  - Estrutura e validação expostas nos runbooks e C4: **PARTIAL (documentação)**.
- **6. Quality & Validation**
  - Smoke test operacional e validação de bundle documentada: **PARTIAL (operacional)**
- **7. Segurança Base**
  - Sem alterações; mantém guardrails existentes: **UNCHANGED**.
- **8. Observabilidade Base**
  - Sem alterações; placeholder Redis documentado: **UNCHANGED**.
- **9. Tenant Zero (Araquem)**
  - Alias e bundle demo cobertos nos runbooks/smoke: **PARTIAL (documentação)**.
- **10. Critério de Saída do Stage 0**
  - Seção dedicada adicionada ao README para rastreabilidade: **DONE (documentação)**.

## Notas
- Nenhum ADR foi alterado.
- Nenhuma dependência nova foi adicionada.
- Scripts adicionados para Linux mantêm paridade funcional com scripts PowerShell existentes.
