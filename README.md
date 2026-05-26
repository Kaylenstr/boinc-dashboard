# BOINC Dashboard

Web dashboard for monitoring BOINC clients over GUI RPC (port 31416).

## Install

```bash
git clone https://github.com/Kaylenstr/boinc-dashboard.git
cd boinc-dashboard
bash install.sh
```

One command after clone. On Debian/Ubuntu the script installs missing system packages (`python3`, `python3-venv`), sets up the app, and starts it. With systemd it runs as your user under `boinc-dashboard.service`.

Open the URL printed at the end.

- `bash run.sh` - foreground (testing)
- `bash stop.sh` - stop background process or systemd service

Install steps: `install/preflight.sh`, `install/setup.sh`, `install/start.sh`.

## Requirements

- Debian/Ubuntu for automatic system package install
- This machine can reach your BOINC clients on the network
- Each client lists this host in `remote_hosts.cfg`

## Security

- RPC passwords are stored encrypted in `data/servers.json` (needs `BOINC_DASHBOARD_KEY`).
- Do not commit `.env` or `data/servers.json`.
- There is no login on the dashboard itself. Keep it on LAN, Tailscale, or behind a proxy with auth.

## Data

Server list lives in `data/servers.json`. Back up `data/` and your `.env` key together.

## BOINC client setup

On each client: add this dashboard host to `remote_hosts.cfg`, set `gui_rpc_auth.cfg`, restart the BOINC client.
