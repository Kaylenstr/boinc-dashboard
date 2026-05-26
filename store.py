import json
import os
import re

from cryptography.fernet import Fernet, InvalidToken

DATA_DIR = os.environ.get("DATA_DIR", "./data")
SERVERS_FILE = os.path.join(DATA_DIR, "servers.json")
SERVER_ID_RE = re.compile(r"^[a-f0-9]{8}$")


class StoreError(Exception):
    pass


class ConfigError(StoreError):
    pass


def _fernet():
    key = os.environ.get("BOINC_DASHBOARD_KEY", "").strip()
    if not key:
        raise ConfigError(
            "BOINC_DASHBOARD_KEY is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode())


def encrypt_secret(value):
    if value is None:
        value = ""
    return _fernet().encrypt(str(value).encode()).decode()


def decrypt_secret(token):
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise StoreError("Could not decrypt stored credentials") from exc


def _migrate_record(server):
    if "password" in server and "secret" not in server:
        server["secret"] = encrypt_secret(server.pop("password"))
    return server


def load_servers():
    if not os.path.exists(SERVERS_FILE):
        return []
    try:
        with open(SERVERS_FILE, "r", encoding="utf-8") as handle:
            servers = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return []

    changed = False
    cleaned = []
    for server in servers:
        if not isinstance(server, dict):
            continue
        if "password" in server:
            changed = True
        cleaned.append(_migrate_record(server))
    if changed:
        save_servers(cleaned)
    return cleaned


def save_servers(servers):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = SERVERS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(servers, handle, indent=2)
    os.replace(tmp, SERVERS_FILE)


def public_server(server):
    return {
        "id": server["id"],
        "name": server["name"],
        "host": server["host"],
        "port": server["port"],
    }


def find_server(server_id):
    if not SERVER_ID_RE.match(server_id or ""):
        return None
    for server in load_servers():
        if server["id"] == server_id:
            return server
    return None


def server_password(server):
    if "secret" not in server:
        raise StoreError("Server credentials are missing")
    return decrypt_secret(server["secret"])
