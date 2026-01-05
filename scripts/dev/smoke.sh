#!/usr/bin/env bash
set -euo pipefail

curl -sf http://localhost:8000/api/v1/runtime/healthz >/dev/null
echo "Healthz runtime OK"

curl -sf http://localhost:8001/api/v1/control/healthz >/dev/null
echo "Healthz control OK"

curl -sf http://localhost:8001/api/v1/control/tenants/demo/bundles/202601050001/validate >/dev/null
echo "Validate bundle OK"

curl -sf -X POST -H "Content-Type: application/json" \
  -d '{"bundle_id":"202601050001"}' \
  http://localhost:8001/api/v1/control/tenants/demo/aliases/current >/dev/null
echo "Set current alias OK"

curl -sf http://localhost:8001/api/v1/control/tenants/demo/aliases >/dev/null
echo "Confirm aliases OK"

curl -sf http://localhost:8001/api/v1/control/tenants/demo/resolve/current >/dev/null
echo "Resolve current OK"

curl -sf -X POST -H "Content-Type: application/json" \
  -d '{"tenant_id":"demo","question":"smoke test"}' \
  http://localhost:8000/api/v1/runtime/ask >/dev/null
echo "Ask current OK"

echo "Smoke test completed"
