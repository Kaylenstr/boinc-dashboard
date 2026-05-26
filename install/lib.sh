#!/usr/bin/env bash

if [ -z "${ROOT:-}" ]; then
  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

apt_install() {
  if ! command -v apt-get >/dev/null 2>&1; then
    return 1
  fi
  if command -v sudo >/dev/null 2>&1 && [ "$(id -u)" -ne 0 ]; then
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y "$@"
  else
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y "$@"
  fi
}

run_privileged() {
  if [ "$(id -u)" -eq 0 ]; then
    "$@"
  elif command -v sudo >/dev/null 2>&1; then
    sudo "$@"
  else
    return 1
  fi
}

app_port() {
  local port
  port="$(grep '^PORT=' "$ROOT/.env" 2>/dev/null | cut -d= -f2 | tr -d '[:space:]')"
  echo "${port:-8770}"
}

show_url() {
  local port ip
  port="$(app_port)"
  ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  if [ -n "$ip" ]; then
    echo "Open http://${ip}:${port}"
  else
    echo "Open http://<server-ip-or-hostname>:${port}"
  fi
}

use_systemd() {
  command -v systemctl >/dev/null 2>&1 || return 1
  systemctl is-system-running >/dev/null 2>&1
}

can_create_venv() {
  local testdir
  testdir="$(mktemp -d)"
  if python3 -m venv "$testdir" >/dev/null 2>&1; then
    rm -rf "$testdir"
    return 0
  fi
  rm -rf "$testdir"
  return 1
}
