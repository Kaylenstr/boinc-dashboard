#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck source=lib.sh
source "$ROOT/install/lib.sh"

cd "$ROOT"

if [ "$(id -u)" -eq 0 ]; then
  echo "Run without sudo: bash install.sh"
  exit 1
fi

ensure_python3() {
  if command -v python3 >/dev/null 2>&1; then
    return 0
  fi
  echo "Installing python3..."
  if ! apt_install python3; then
    echo "python3 is required. Supported auto-install: Debian/Ubuntu (apt)."
    exit 1
  fi
}

ensure_venv_support() {
  if can_create_venv; then
    return 0
  fi
  local ver
  ver="$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')"
  echo "Installing python3-venv..."
  if apt_install "python${ver}-venv" 2>/dev/null; then
    return 0
  fi
  if ! apt_install python3-venv; then
    echo "python3-venv is required. Supported auto-install: Debian/Ubuntu (apt)."
    exit 1
  fi
}

echo "Checking system packages..."
ensure_python3
ensure_venv_support

if ! can_create_venv; then
  echo "Could not create a Python virtual environment."
  exit 1
fi

echo "System packages OK"
