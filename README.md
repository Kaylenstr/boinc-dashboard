# BOINC Dashboard

Web dashboard for monitoring BOINC clients over GUI RPC (port 31416).

## Requirements

- Python 3.10+
- This machine can reach your BOINC clients on the network
- Each client lists this host in `remote_hosts.cfg`

## Install

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux

pip install -r requirements.txt
copy .env.example .env        # Windows
# cp .env.example .env        # Linux
```

Generate a key for `.env`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Minimum settings:

```
BOINC_DASHBOARD_KEY=your-generated-key
DATA_DIR=./data
PORT=8770
```

Load env vars and start (PowerShell example):

```powershell
Get-Content .env | ForEach-Object {
  if ($_ -match '^(.*?)=(.*)$') { Set-Item -Path env:$($matches[1]) -Value $matches[2] }
}
python app.py
```

Open http://127.0.0.1:8770

## Security

- RPC passwords are stored encrypted in `data/servers.json` (needs `BOINC_DASHBOARD_KEY`).
- Do not commit `.env` or `data/servers.json`.
- There is no login on the dashboard itself. Keep it on LAN, Tailscale, or behind a proxy with auth.
- Old plain `password` fields in `servers.json` are converted to encrypted `secret` on first load.

## Data

Server list lives in `data/servers.json`. Back up `data/` and your `.env` key together.

## BOINC client setup

On each client: add this dashboard host to `remote_hosts.cfg`, set `gui_rpc_auth.cfg`, restart the BOINC client.
