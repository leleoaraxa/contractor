#!/usr/bin/env bash
set -euo pipefail

API_KEY="${CONTRACTOR_API_KEY:-${CONTRACTOR_API_KEYS:-}}"
AUTH_HEADER=()

if [[ "${CONTRACTOR_AUTH_DISABLED:-0}" != "1" ]]; then
  if [[ -z "${API_KEY}" ]]; then
    echo "Set CONTRACTOR_API_KEYS (comma-separated) or CONTRACTOR_API_KEY when auth is enabled."
    exit 1
  fi
  AUTH_HEADER=(-H "X-API-Key: ${API_KEY%%,*}")
fi

curl -sf "${AUTH_HEADER[@]}" http://localhost:8000/api/v1/runtime/healthz >/dev/null
echo "Healthz runtime OK"

curl -sf "${AUTH_HEADER[@]}" http://localhost:8001/api/v1/control/healthz >/dev/null
echo "Healthz control OK"

curl -sf "${AUTH_HEADER[@]}" \
  http://localhost:8001/api/v1/control/tenants/demo/bundles/202601050001/validate >/dev/null
echo "Validate bundle OK"

curl -sf -X POST -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{"bundle_id":"202601050001"}' \
  http://localhost:8001/api/v1/control/tenants/demo/aliases/current >/dev/null
echo "Set current alias OK"

curl -sf "${AUTH_HEADER[@]}" http://localhost:8001/api/v1/control/tenants/demo/aliases >/dev/null
echo "Confirm aliases OK"

curl -sf "${AUTH_HEADER[@]}" http://localhost:8001/api/v1/control/tenants/demo/resolve/current >/dev/null
echo "Resolve current OK"

curl -sf -X POST -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{"tenant_id":"demo","question":"smoke test"}' \
  http://localhost:8000/api/v1/runtime/ask >/dev/null
echo "Ask current OK"

echo "Smoke test completed"
