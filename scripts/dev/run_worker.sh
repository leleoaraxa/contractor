#!/usr/bin/env bash
set -eu
if [ -n "${BASH_VERSION:-}" ]; then
  set -o pipefail
fi

export PYTHONPATH="${PYTHONPATH:-.}"

python -m app.runtime.worker.main
