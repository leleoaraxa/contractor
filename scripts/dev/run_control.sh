#!/usr/bin/env bash
set -euo pipefail

python -m uvicorn app.control_plane.api.main:app --host 0.0.0.0 --port 8001 --reload
