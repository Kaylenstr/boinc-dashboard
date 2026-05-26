#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if [ ! -x .venv/bin/python ]; then
  bash "$ROOT/install.sh" --no-start
fi

exec .venv/bin/python app.py
