# Security Baseline Report — CONTRACTOR

## Scope
- Implements minimal API-key authentication for Control Plane and Runtime (ADR 0007).
- Introduces tenant-aware token-bucket rate limiting backed by Redis with in-memory fallback (ADR 0013).
- Adds audit logging for alias changes and promotion/quality runs.

## Authentication & Authorization
- **Header:** `X-API-Key` required on Control Plane alias/resolve/validate/quality endpoints and Runtime `/ask`.
- **Config:** `CONTRACTOR_API_KEYS` (comma-separated). First key is reused by Runtime when calling Control Plane.
- **Dev override:** `CONTRACTOR_AUTH_DISABLED=1` disables API-key checks only for local/dev usage.
- Unauthorized requests return `401/403`; missing configuration surfaces a clear 401 with guidance.

## Rate Limiting
- **Defaults:** `RATE_LIMIT_RPS=10`, `RATE_LIMIT_BURST=20`.
- **Backend:** `RATE_LIMIT_REDIS_URL` (or `RUNTIME_REDIS_URL`) for Redis token bucket; automatic fallback to in-memory with warning log.
- **Scope:** per-tenant keys including endpoint scope (control aliases/validate/quality, runtime /ask).
- **Response:** HTTP `429` with `Retry-After` header and JSON body `{ "error": "rate_limit_exceeded", "retry_after_seconds": <int> }`.

## Audit Logging
- **File:** `registry/control_plane/audit.log` (JSONL).
- **Events captured:** alias changes (old/new bundle IDs) and promotion/quality runs (status and counts).
- **Data hygiene:** payloads redacted for sensitive patterns before persistence.

## Developer Experience
- Smoke scripts (`scripts/dev/smoke.*`) automatically inject `X-API-Key` when auth is enabled; fail fast when missing configuration.
- Runbooks updated with auth headers, rate-limit knobs, and dev toggle instructions.
- Runtime Control Plane client propagates API key automatically to keep alias resolution working under auth.
