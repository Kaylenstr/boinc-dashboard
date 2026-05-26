#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib.sh
source "$ROOT/install/lib.sh"

cd "$ROOT"

bash "$ROOT/install/stop.sh" >/dev/null 2>&1 || true

install_systemd_service() {
  local unit user
  unit="/etc/systemd/system/boinc-dashboard.service"
  user="$(id -un)"

  sed -e "s|@INSTALL_DIR@|${ROOT}|g" -e "s|@INSTALL_USER@|${user}|g" \
    "$ROOT/install/boinc-dashboard.service" | run_privileged tee "$unit" >/dev/null

  run_privileged systemctl daemon-reload
  run_privileged systemctl enable --now boinc-dashboard

  echo "Service running (systemd)"
  show_url
}

start_background() {
  if [ -f .dashboard.pid ] && kill -0 "$(cat .dashboard.pid)" 2>/dev/null; then
    echo "Already running (PID $(cat .dashboard.pid))"
  else
    nohup .venv/bin/python app.py >> dashboard.log 2>&1 &
    echo $! > .dashboard.pid
    echo "Started in background (PID $(cat .dashboard.pid))"
  fi
  show_url
}

echo "Starting..."
if use_systemd; then
  install_systemd_service
else
  start_background
fi
