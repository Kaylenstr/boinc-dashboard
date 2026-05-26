#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib.sh
source "$ROOT/install/lib.sh"

cd "$ROOT"

if [ -f .dashboard.pid ]; then
  pid="$(cat .dashboard.pid)"
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid"
    echo "Stopped PID $pid"
  fi
  rm -f .dashboard.pid
fi

if use_systemd; then
  run_privileged systemctl stop boinc-dashboard 2>/dev/null || true
fi
