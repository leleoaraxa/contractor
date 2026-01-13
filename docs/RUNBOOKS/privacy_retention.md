# Runbook — Privacidade e retenção (Stage 2)

> Referência: ADR 0021 — Product roadmap e maturity stages.

## 1) Reduzir/evitar logging de payloads sensíveis
- **Nunca** logar `X-API-Key` ou headers de autenticação.
- Evite logar `question` em plaintext por default; use logs estruturados mínimos (status, tempo, IDs).
- Quando necessário, use redaction e remova payloads em logs de erro.

## 2) Onde configurar retenção
- **Logs (stdout/container)**: depende do runtime (Docker/Kubernetes). Configure retenção no log driver ou agente (ex.: logrotate).
- **Métricas Prometheus**: configurar `--storage.tsdb.retention.time` no servidor Prometheus.
- **Audit log**: arquivo local `registry/control_plane/audit.log`.
- **Cache runtime (Redis)**: TTL aplicado via policy; sem retenção de longo prazo.

## 3) Purge/limpeza — procedimentos manuais

### 3.1 Logs de aplicação (stdout)
- Rotação/expurgo deve ser feito pelo operador conforme infra.
- Exemplo (Docker):
  ```bash
  docker compose logs --since 1h > /tmp/contractor-logs-1h.txt
  # Ajuste o log driver/rotacionamento conforme política local
  ```

### 3.2 Audit log (control plane)
- Arquivo: `registry/control_plane/audit.log`
- Procedimento seguro (Stage 2, manual):
  1. **Pare o serviço do control plane** para evitar escrita concorrente.
  2. Faça backup do arquivo atual.
  3. Trunque o arquivo.
  4. Reinicie o control plane.
- Exemplo:
  ```bash
  docker compose stop control
  mkdir -p archive/audit
  cp registry/control_plane/audit.log archive/audit/audit-$(date +%F).log
  : > registry/control_plane/audit.log
  docker compose start control
  ```
- Alternativa (se não for possível parar o serviço): faça backup, trunque rapidamente e valide que o processo reabriu o arquivo; registre a evidência da operação.
- Truncar após o período definido (apenas se o serviço estiver parado):
  ```bash
  : > registry/control_plane/audit.log
  ```

### 3.3 Cache runtime
- **Redis** (se habilitado via `RUNTIME_REDIS_URL`):
  - **Opção A (dev/test apenas, destrutiva)**: limpar toda a base do Redis usada pelo runtime.
    ```bash
    redis-cli FLUSHDB
    ```
  - **Opção B (se existir prefixo documentado)**: usar `SCAN` com o prefixo real e **somente** então remover chaves específicas.
    - Se não houver prefixo documentado, **não** executar purge seletivo para evitar remoções erradas.
    ```bash
    # Exemplo genérico — substitua <PREFIXO_REAL_DOCUMENTADO>
    redis-cli --scan --pattern '<PREFIXO_REAL_DOCUMENTADO>*' | xargs -r redis-cli del
    ```
- **In-memory**: reinicie o serviço do runtime para limpar o cache.
  ```bash
  docker compose restart runtime
  ```

## 4) Evidências para auditoria
- Snapshot da configuração de retenção (log driver / Prometheus flags).
- Registro das execuções de purge (data, operador, comandos usados).
- Retention.yaml no repositório (documenta defaults de Stage 2).

## 5) Limitações (Stage 2)
- Retenção manual/semi-manual; automação completa é Stage 3+.
- Não há DLP, eDiscovery ou criptografia por tenant.
