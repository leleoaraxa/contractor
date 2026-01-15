# Logs sem payload sensível (non-prod)

## Escopo (non-prod)

Evidência coletada localmente via `TestClient` (FastAPI) em ambiente **non-prod**. Não há qualquer alegação de comportamento em produção.

## Referências

- ADR 0027: `docs/ADR/0027-enterprise-access-control-and-identity.md`
- ADR 0028: `docs/ADR/0028-stage-3-completion-and-readiness-checklist.md`
- Runbook: `docs/RUNBOOKS/privacy_retention.md`

## Commands executed (compose/local)

```bash
python - <<'PY'
import importlib
import logging
import os
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ["CONTRACTOR_API_KEYS"] = "tenant-alpha:tenant_runtime_client:log-evidence-key"
os.environ["RUNTIME_DEDICATED_TENANT_ID"] = "tenant-alpha"

for module_name in (
    "app.runtime.api.main",
    "app.runtime.api.routers.ask",
    "app.runtime.engine.runtime_identity",
    "app.shared.config.settings",
):
    if module_name in sys.modules:
        del sys.modules[module_name]

import app.shared.config.settings as settings_module

importlib.reload(settings_module)

from app.runtime.api.main import app as runtime_app
from app.runtime.engine.ask_models import AskResponse

client = TestClient(runtime_app)

with patch("app.runtime.api.routers.ask.prepare_ask") as mock_prepare:
    mock_prepare.return_value = (AskResponse(answer="ok", meta={}), None)
    response = client.post(
        "/api/v1/runtime/ask",
        headers={"X-API-Key": "log-evidence-key"},
        json={"tenant_id": "tenant-alpha", "question": "super-secret-payload"},
    )
    print("runtime_status", response.status_code)

logger = logging.getLogger("runtime.ask")
logger.info(
    "runtime.request payload=%s",
    {
        "question": "super-secret-payload",
        "prompt": "do-not-log",
        "content": "raw-content",
        "body": {"nested": "payload"},
        "payload": {"question": "nested-question"},
    },
)
PY
```

```bash
python - <<'PY'
import hashlib
import importlib
import json
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

audit_path = Path("/tmp/control_audit.log")
alias_store_path = Path("/tmp/tenant_aliases.json")

os.environ["CONTROL_AUDIT_LOG_PATH"] = str(audit_path)
os.environ["CONTROL_ALIAS_STORE_PATH"] = str(alias_store_path)
os.environ["CONTRACTOR_API_KEYS"] = "audit-key"

for module_name in [
    "app.control_plane.api.routers.tenants",
    "app.control_plane.api.routers.versions",
    "app.control_plane.api.routers.bundles",
    "app.control_plane.api.routers.quality",
    "app.control_plane.api.routers.healthz",
    "app.control_plane.api.main",
    "app.shared.config.settings",
]:
    if module_name in sys.modules:
        del sys.modules[module_name]

import app.shared.config.settings as settings_module

importlib.reload(settings_module)

from app.control_plane.api.main import create_app

app = create_app()
client = TestClient(app)

response = client.put(
    "/api/v1/control/tenants/demo/versions/draft",
    headers={"X-API-Key": "audit-key"},
    json={"bundle_id": "202601050001"},
)
print("control_status", response.status_code)

lines = audit_path.read_text(encoding="utf-8").strip().splitlines()
record = json.loads(lines[-1])
print("audit_log", json.dumps(record, ensure_ascii=False))
print(
    "actor",
    record["actor"],
    "expected_prefix",
    hashlib.sha256("audit-key".encode("utf-8")).hexdigest()[:12],
)
PY
```

## Observed output (redacted)

```
rate limiter: Redis not configured, using in-memory backend
{"ts": "2026-01-15T12:08:33.245868+00:00", "level": "INFO", "logger": "httpx", "msg": "HTTP Request: POST http://testserver/api/v1/runtime/ask \"HTTP/1.1 200 OK\""}
runtime_status 200
{"ts": "2026-01-15T12:08:33.246949+00:00", "level": "INFO", "logger": "runtime.ask", "msg": "runtime.request [REDACTED], [REDACTED], [REDACTED], [REDACTED]}, [REDACTED]}"}
```

```
rate limiter: Redis not configured, using in-memory backend
{"ts": "2026-01-15T12:08:44.083122+00:00", "level": "INFO", "logger": "httpx", "msg": "HTTP Request: PUT http://testserver/api/v1/control/tenants/demo/versions/draft \"HTTP/1.1 200 OK\""}
control_status 200
audit_log {"ts": "2026-01-15T12:08:44.076644+00:00", "action": "alias.set", "event": "alias.set", "tenant_id": "demo", "actor": "key_hash:b693cf9c437f", "target": {"alias": "draft", "bundle_id": "202601050001"}, "previous_bundle_id": "202601050001"}
actor key_hash:b693cf9c437f expected_prefix b693cf9c437f
```

## What this proves

- O runtime e o control plane em **non-prod** registram eventos sem incluir payload sensível (`question`, `prompt`, `content`, `body`, `payload`) nos logs observados.
- A redaction/enforcement é aplicada de forma centralizada no logging.

## What this does NOT prove

- Não prova comportamento em produção.
- Não valida retenção nem integração com sistemas externos de observabilidade.
