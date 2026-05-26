#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required"
  exit 1
fi

python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  KEY="$(.venv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")"
  sed -i "s|replace-with-output-of-fernet-generate-key|${KEY}|" .env
  echo "Created .env with a new BOINC_DASHBOARD_KEY"
else
  echo ".env already exists, left unchanged"
fi

mkdir -p data

if [ "${1:-}" = "--service" ]; then
  UNIT="/etc/systemd/system/boinc-dashboard.service"
  sed "s|@INSTALL_DIR@|${ROOT}|g" boinc-dashboard.service | sudo tee "$UNIT" >/dev/null
  sudo systemctl daemon-reload
  sudo systemctl enable --now boinc-dashboard
  echo "Service installed. Status: sudo systemctl status boinc-dashboard"
  exit 0
fi

echo
echo "Install done."
echo "  ./run.sh"
echo "  http://<server-ip-or-hostname>:8770"
echo
echo "Optional systemd service:"
echo "  ./install.sh --service"
