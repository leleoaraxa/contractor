# CONTRACTOR

## O que é
O CONTRACTOR é um **SaaS B2B** que atua como **Control Plane para sistemas de IA governados**, com separação explícita entre Control Plane e Runtime.

Ele permite versionar, validar, promover e operar artefatos de IA de forma determinística, auditável e segura em ambientes multi-tenant.

A descrição completa do produto está em:
- 👉 [`docs/PRODUCT.md`](docs/PRODUCT.md)

---

## Fontes de verdade
Este repositório é governado por documentação explícita.
Antes de alterar código, leia:

- **Estado atual do projeto:**
  - 👉 [`docs/STATUS.md`](docs/STATUS.md)

- **Arquitetura:**
  - 👉 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

- **Decisões arquiteturais (ADRs):**
  - 👉 [`docs/adr/`](docs/adr/)

---

## Como navegar no repositório
```

contractor/
├── app/        # Código da aplicação (Control Plane / Runtime)
├── docs/       # Fonte de verdade (produto, arquitetura, ADRs)
├── ops/        # Infra, deploy, observabilidade (quando aplicável)
└── README.md

```

---

## Como rodar testes

### Local (venv)
```bash
python -m venv .venv
# linux/mac:
source .venv/bin/activate
# windows (powershell):
# .\.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
pytest -q

```

### Docker

```bash
docker compose build
docker compose run --rm tests
```

### Smoke / integração (se aplicável)

```bash
./scripts/dev/smoke.sh
```

> Caso não exista smoke test ainda, isso será introduzido quando o runtime mínimo estiver definido.

---

## Contribuição

* Toda mudança relevante exige **PR atômica**
* PRs devem seguir o template obrigatório
* Decisões estruturais exigem **ADR**
* Toda entrega deve atualizar `docs/STATUS.md`
