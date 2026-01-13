# Contractor SDK (Python) — Stage 2

Este SDK Python é o cliente oficial mínimo para o Stage 2 (Production Ready) conforme **ADR 0021**.
Ele é propositalmente simples, versionado e documentado, sem automações complexas ou garantias enterprise.

## O que é suportado (Stage 2)

Endpoints públicos e estáveis cobertos:

**Runtime**
- `POST /api/v1/runtime/ask` com payload canônico: `{"tenant_id": "...", "question": "...", "bundle_id": "..."}`.

**Control**
- `GET /api/v1/control/healthz`
- `POST /api/v1/control/tenants/{tenant_id}/aliases/current`
- `GET /api/v1/control/tenants/{tenant_id}/versions/current/resolve`
- `GET /api/v1/control/tenants/{tenant_id}/resolve/current`

## O que NÃO faz parte do SDK no Stage 2

- SDKs para outras linguagens
- Streaming
- Retries automáticos
- Cobertura de todos os endpoints
- Geração automática avançada (OpenAPI generators complexos)
- Garantias enterprise (Stage 3)

## Instalação local

Este pacote é local e versionado (não publicado no PyPI neste estágio).

Dependência mínima: `requests`.

```bash
cd sdk/python
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuração

```python
from contractor_sdk import ContractorClient, SDKConfig, RuntimeClient, ControlClient

config = SDKConfig(
    base_url="https://api.seu-ambiente",
    api_key="sua-api-key",
    timeout=30.0,
)
client = ContractorClient(config)

runtime = RuntimeClient(client)
control = ControlClient(client)
```

## Exemplos

### Runtime: /ask

```python
response = runtime.ask(
    {
        "tenant_id": "tenant-123",
        "question": "Explain Stage 2 SDKs",
        "bundle_id": "bundle-abc",
    }
)
print(response)
```

### Control: rollback manual (alias current)

```python
payload = {
    "bundle_id": "bundle-anterior",
}
response = control.set_current_alias("tenant-123", payload)
print(response)
```

## Semântica e comportamento

- Timeouts são configuráveis via `SDKConfig.timeout`.
- **Sem retries automáticos** (responsabilidade do caller no Stage 2).
- Erros HTTP:
  - `4xx` → `ClientError`
  - `5xx` → `ServerError`
- Respostas retornadas como `dict`.

## Versionamento e estabilidade

Versão inicial: **v0.1.0**

Política (Stage 2):
- Sem breaking changes sem bump de versão.
- Mudanças incompatíveis → nova versão major.

## Referências

- ADR 0021 — SDKs estáveis (Stage 2)
