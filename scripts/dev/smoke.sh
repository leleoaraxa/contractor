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
  local extra_header="${4:-}"
  local extra_args=()
  if [[ -n "$extra_header" ]]; then
    extra_args=(-H "$extra_header")
  fi
  RESPONSE_BODY="$(mktemp)"
  if [[ -n "$data" ]]; then
    RESPONSE_STATUS="$(curl -s -w "%{http_code}" -o "$RESPONSE_BODY" \
      -X "$method" -H "Content-Type: application/json" "${AUTH_HEADER[@]}" "${extra_args[@]}" \
      -d "$data" "$url")"
  else
    RESPONSE_STATUS="$(curl -s -w "%{http_code}" -o "$RESPONSE_BODY" \
      -X "$method" "${AUTH_HEADER[@]}" "${extra_args[@]}" "$url")"
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
if [[ "$RESPONSE_STATUS" != "200" ]]; then
  echo "Unexpected status for first ask: ${RESPONSE_STATUS} (expected 200)"
  if [[ -s "$RESPONSE_BODY" ]]; then
    cat "$RESPONSE_BODY"
  else
    echo "<empty>"
  fi
  if [[ "$RESPONSE_STATUS" == "500" ]]; then
    rm -f "$RESPONSE_BODY"
    request_json POST "$RUNTIME_BASE/api/v1/runtime/ask" "$ask_payload" "X-Explain: 1"
    echo "X-Explain status: ${RESPONSE_STATUS}"
    if [[ -s "$RESPONSE_BODY" ]]; then
      cat "$RESPONSE_BODY"
    else
      echo "<empty>"
    fi
  fi
  rm -f "$RESPONSE_BODY"
  exit 1
fi
rm -f "$RESPONSE_BODY"

rate_limited=0
max_attempts=25
sleep_seconds=0.075
for ((attempt = 1; attempt <= max_attempts; attempt++)); do
  request_json POST "$RUNTIME_BASE/api/v1/runtime/ask" "$ask_payload"
  if [[ "$RESPONSE_STATUS" == "200" ]]; then
    rm -f "$RESPONSE_BODY"
    sleep "$sleep_seconds"
    continue
  fi
  if [[ "$RESPONSE_STATUS" == "429" ]]; then
    rate_limited=1
    break
  fi
  echo "Unexpected status during rate limit probe: ${RESPONSE_STATUS}"
  if [[ -s "$RESPONSE_BODY" ]]; then
    cat "$RESPONSE_BODY"
  else
    echo "<empty>"
  fi
  if [[ "$RESPONSE_STATUS" == "500" ]]; then
    rm -f "$RESPONSE_BODY"
    request_json POST "$RUNTIME_BASE/api/v1/runtime/ask" "$ask_payload" "X-Explain: 1"
    echo "X-Explain status: ${RESPONSE_STATUS}"
    if [[ -s "$RESPONSE_BODY" ]]; then
      cat "$RESPONSE_BODY"
    else
      echo "<empty>"
    fi
  fi
  rm -f "$RESPONSE_BODY"
  exit 1
done

if [[ "$rate_limited" -ne 1 ]]; then
  rm -f "$RESPONSE_BODY"
  echo "rate limit not triggered; adjust RATE_LIMIT_RPS/RATE_LIMIT_BURST or policy"
  exit 1
fi

echo "Body:"
cat "$RESPONSE_BODY"
python - "$RESPONSE_BODY" <<'PY'
import json
import sys

try:
    data = json.load(open(sys.argv[1]))
except json.JSONDecodeError:
    sys.exit(2)

detail = data.get("detail") or {}
if detail.get("error") != "rate_limit_exceeded":
    sys.exit(3)
PY
status=$?
if [[ "$status" -eq 2 ]]; then
  echo "429 received but body is not valid JSON"
  cat "$RESPONSE_BODY"
  rm -f "$RESPONSE_BODY"
  exit 1
fi
if [[ "$status" -eq 3 ]]; then
  echo "429 received but detail.error is not rate_limit_exceeded"
  cat "$RESPONSE_BODY"
  rm -f "$RESPONSE_BODY"
  exit 1
fi
rm -f "$RESPONSE_BODY"
echo "Rate limit OK"

echo "Smoke test completed"
