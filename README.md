# BOINC Dashboard

Web dashboard for monitoring BOINC clients over GUI RPC (port 31416).

## Requirements

- Python 3.10+
- This machine can reach your BOINC clients on the network
- Each client lists this host in `remote_hosts.cfg`

## Quick install (Linux)

```bash
chmod +x install.sh run.sh
./install.sh
./run.sh
```

Open `http://<server-ip-or-hostname>:8770`

Run on boot (systemd):

```bash
./install.sh --service
```

The install script creates `.venv`, installs dependencies, generates `BOINC_DASHBOARD_KEY` in `.env` if missing, and creates `data/`.

## Manual install

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Generate a key and put it in `.env`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

```
BOINC_DASHBOARD_KEY=your-generated-key
DATA_DIR=./data
PORT=8770
```

```bash
python app.py
```

The app reads `.env` on startup and listens on all interfaces (`0.0.0.0`).

## Security

- RPC passwords are stored encrypted in `data/servers.json` (needs `BOINC_DASHBOARD_KEY`).
- Do not commit `.env` or `data/servers.json`.
- There is no login on the dashboard itself. Keep it on LAN, Tailscale, or behind a proxy with auth.
- Old plain `password` fields in `servers.json` are converted to encrypted `secret` on first load.

## Data

Server list lives in `data/servers.json`. Back up `data/` and your `.env` key together.

## BOINC client setup

On each client: add this dashboard host to `remote_hosts.cfg`, set `gui_rpc_auth.cfg`, restart the BOINC client.
