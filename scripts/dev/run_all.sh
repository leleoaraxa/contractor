#!/usr/bin/env bash
set -euo pipefail

python -m uvicorn app.control_plane.api.main:app --host 0.0.0.0 --port 8001 --reload &
CONTROL_PID=$!

python -m uvicorn app.runtime.api.main:app --host 0.0.0.0 --port 8000 --reload &
RUNTIME_PID=$!

trap 'kill $CONTROL_PID $RUNTIME_PID 2>/dev/null || true' EXIT

wait
