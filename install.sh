#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
NO_START=0

for arg in "$@"; do
  if [ "$arg" = "--no-start" ]; then
    NO_START=1
  fi
done

bash "$ROOT/install/preflight.sh"
bash "$ROOT/install/setup.sh"

if [ "$NO_START" -eq 0 ]; then
  bash "$ROOT/install/start.sh"
else
  echo "Install done. Start with: bash run.sh"
fi
