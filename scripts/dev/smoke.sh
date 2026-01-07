#!/usr/bin/env bash
set -euo pipefail

is_truthy() {
  local value="$1"
  shopt -s nocasematch
  [[ "$value" == "1" || "$value" == "true" || "$value" == "yes" || "$value" == "y" || "$value" == "on" ]]
}

first_non_empty_token() {
  local raw="$1"
  IFS=',' read -ra parts <<<"$raw"
  for token in "${parts[@]}"; do
    local trimmed="${token#"${token%%[![:space:]]*}"}"
    trimmed="${trimmed%"${trimmed##*[![:space:]]}"}"
    if [[ -n "$trimmed" ]]; then
      echo "$trimmed"
      return
    fi
  done
}

API_KEY="$(first_non_empty_token "${CONTRACTOR_API_KEY:-}")"
if [[ -z "$API_KEY" ]]; then
  API_KEY="$(first_non_empty_token "${CONTRACTOR_API_KEYS:-}")"
fi
AUTH_HEADER=()
CONTROL_BASE="${CONTROL_BASE_URL:-http://localhost:8001}"
RUNTIME_BASE="${RUNTIME_BASE_URL:-http://localhost:8000}"

normalize_base() {
  local base="$1"
  local suffix="$2"
  base="${base%/}"
  if [[ "$base" == *"$suffix" ]]; then
    base="${base%$suffix}"
    base="${base%/}"
  fi
  echo "$base"
}

CONTROL_BASE="$(normalize_base "$CONTROL_BASE" "/api/v1/control/healthz")"
CONTROL_BASE="$(normalize_base "$CONTROL_BASE" "/api/v1/control")"
RUNTIME_BASE="$(normalize_base "$RUNTIME_BASE" "/api/v1/runtime/healthz")"
RUNTIME_BASE="$(normalize_base "$RUNTIME_BASE" "/api/v1/runtime")"

if ! is_truthy "${CONTRACTOR_AUTH_DISABLED:-0}"; then
  if [[ -z "${API_KEY}" ]]; then
    API_KEY="dev-key"
    echo "WARNING: CONTRACTOR_API_KEY(S) not set; using fallback dev-key."
  fi
  AUTH_HEADER=(-H "X-API-Key: $API_KEY")
fi

request_json() {
  local method="$1"
  local url="$2"
  local data="${3:-}"
  RESPONSE_BODY="$(mktemp)"
  if [[ -n "$data" ]]; then
    RESPONSE_STATUS="$(curl -s -w "%{http_code}" -o "$RESPONSE_BODY" \
      -X "$method" -H "Content-Type: application/json" "${AUTH_HEADER[@]}" \
      -d "$data" "$url")"
  else
    RESPONSE_STATUS="$(curl -s -w "%{http_code}" -o "$RESPONSE_BODY" \
      -X "$method" "${AUTH_HEADER[@]}" "$url")"
  fi
}

assert_status() {
  local expected="$1"
  local context="$2"
  if [[ "$RESPONSE_STATUS" != "$expected" ]]; then
    echo "Unexpected status for ${context}: ${RESPONSE_STATUS} (expected ${expected})"
    cat "$RESPONSE_BODY"
    rm -f "$RESPONSE_BODY"
    exit 1
  fi
}

check_healthz() {
  local url="$1"
  local message="$2"
  if ! curl -sSf "${AUTH_HEADER[@]}" "$url" >/dev/null; then
    echo "Suba: ${message}"
    echo "Health check failed: $url"
    exit 1
  fi
}

check_healthz "$CONTROL_BASE/api/v1/control/healthz" "docker compose up -d redis control"
check_healthz "$RUNTIME_BASE/api/v1/runtime/healthz" "docker compose up -d redis runtime"

python scripts/quality/smoke_quality_gate.py \
  --tenant-id demo \
  --control-base "$CONTROL_BASE" \
  --runtime-base "$RUNTIME_BASE"

echo "Promotion PASS (bundle 202601050001)..."
request_json POST "$CONTROL_BASE/api/v1/control/tenants/demo/aliases/candidate" \
  '{"bundle_id":"202601050001"}'
assert_status 200 "set candidate"
python - "$RESPONSE_BODY" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
assert data.get("candidate") == "202601050001", data
PY
rm -f "$RESPONSE_BODY"

request_json POST "$CONTROL_BASE/api/v1/control/tenants/demo/aliases/current" \
  '{"bundle_id":"202601050001"}'
assert_status 200 "set current"
python - "$RESPONSE_BODY" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
assert data.get("current") == "202601050001", data
PY
rm -f "$RESPONSE_BODY"
echo "Promotion PASS OK"

echo "Promotion FAIL (template safety, bundle 202601050002)..."
request_json POST "$CONTROL_BASE/api/v1/control/tenants/demo/aliases/candidate" \
  '{"bundle_id":"202601050002"}'
assert_status 400 "promotion gate fail"
python - "$RESPONSE_BODY" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
detail = data.get("detail") or {}
assert detail.get("gate") == "template_safety", data
PY
rm -f "$RESPONSE_BODY"
echo "Template safety gate OK"

echo "Rate limit enforcement (bundle 202601050003)..."
ask_payload='{"tenant_id":"demo","question":"smoke test","bundle_id":"202601050003","release_alias":"current"}'
request_json POST "$RUNTIME_BASE/api/v1/runtime/ask" "$ask_payload"
assert_status 200 "first ask"
rm -f "$RESPONSE_BODY"

request_json POST "$RUNTIME_BASE/api/v1/runtime/ask" "$ask_payload"
assert_status 429 "second ask (rate limit)"
python - "$RESPONSE_BODY" <<'PY'
import json, sys
data = json.load(open(sys.argv[1]))
detail = data.get("detail") or {}
assert detail.get("error") == "rate_limit_exceeded", data
PY
rm -f "$RESPONSE_BODY"
echo "Rate limit OK"

echo "Smoke test completed"
