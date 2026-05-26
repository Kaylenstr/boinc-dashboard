#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib.sh
source "$ROOT/install/lib.sh"

cd "$ROOT"

fix_broken_venv() {
  if [ ! -d .venv ]; then
    return
  fi
  if { [ -x .venv/bin/python ] || [ -x .venv/bin/python3 ]; } && [ -w .venv ]; then
    return
  fi
  echo "Removing broken or root-owned .venv..."
  if run_privileged rm -rf .venv; then
    return
  fi
  echo "Remove .venv manually and run again."
  exit 1
}

ensure_env() {
  if [ ! -f .env ]; then
    cp .env.example .env
  fi
  if grep -q 'replace-with-output-of-fernet-generate-key' .env; then
    KEY="$(.venv/bin/python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")"
    sed -i "s|replace-with-output-of-fernet-generate-key|${KEY}|" .env
  fi
}

echo "Setting up application..."
fix_broken_venv

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi

.venv/bin/pip install -q -r requirements.txt
ensure_env
mkdir -p data
echo "Application ready"
