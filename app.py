import os
import re
import uuid
import threading

from flask import Flask, request, jsonify, render_template

from boinc_rpc import BoincRPC, BoincError, BoincAuthError
import store


def _load_dotenv():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            if key and key not in os.environ:
                os.environ[key] = value.strip()


_load_dotenv()

DATA_DIR = os.environ.get("DATA_DIR", "./data")
store.DATA_DIR = DATA_DIR
store.SERVERS_FILE = os.path.join(DATA_DIR, "servers.json")

if not os.environ.get("BOINC_DASHBOARD_KEY", "").strip():
    raise SystemExit(
        "BOINC_DASHBOARD_KEY is required. "
        "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )

app = Flask(__name__)
_lock = threading.Lock()
_HOST_RE = re.compile(r"^[a-zA-Z0-9.\-:]+$")


def _validate_host(host):
    host = (host or "").strip()
    if not host or len(host) > 253 or not _HOST_RE.match(host):
        return None
    return host


@app.after_request
def _security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/servers", methods=["GET"])
def list_servers():
    return jsonify([store.public_server(item) for item in store.load_servers()])


@app.route("/api/servers", methods=["POST"])
def add_server():
    data = request.get_json(force=True, silent=True) or {}
    host = _validate_host(data.get("host"))
    name = (data.get("name") or host or "").strip()[:80]
    try:
        port = int(data.get("port") or 31416)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid port"}), 400
    password = data.get("password") or ""

    if not host:
        return jsonify({"error": "Host is required"}), 400
    if port < 1 or port > 65535:
        return jsonify({"error": "Invalid port"}), 400

    try:
        with BoincRPC(host, port, password, timeout=8):
            pass
    except BoincAuthError:
        return jsonify({"error": "Connected, but the GUI RPC password is wrong"}), 400
    except (BoincError, OSError) as exc:
        return jsonify({"error": "Could not connect: {}".format(exc)}), 400

    server = {
        "id": uuid.uuid4().hex[:8],
        "name": name or host,
        "host": host,
        "port": port,
        "secret": store.encrypt_secret(password),
    }

    with _lock:
        servers = store.load_servers()
        servers.append(server)
        store.save_servers(servers)

    return jsonify(store.public_server(server)), 201


@app.route("/api/servers/<server_id>", methods=["DELETE"])
def delete_server(server_id):
    with _lock:
        servers = store.load_servers()
        filtered = [item for item in servers if item["id"] != server_id]
        if len(filtered) == len(servers):
            return jsonify({"error": "Not found"}), 404
        store.save_servers(filtered)
    return jsonify({"ok": True})


@app.route("/api/servers/<server_id>/status", methods=["GET"])
def server_status(server_id):
    server = store.find_server(server_id)
    if not server:
        return jsonify({"error": "Not found"}), 404

    try:
        password = store.server_password(server)
        with BoincRPC(server["host"], server["port"], password, timeout=10) as rpc:
            projects = rpc.get_project_status()
            results = rpc.get_results()
            payload = {
                "online": True,
                "cc_status": rpc.get_cc_status(),
                "host": rpc.get_host_info(),
                "projects": projects,
                "results": results,
                "summary": {
                    "tasks_total": len(results),
                    "running": sum(1 for item in results if item["active"] and item["active_task_state"] == 1),
                    "suspended": sum(1 for item in results if item["active_task_state"] == 9),
                    "jobs_done": sum(item["njobs_success"] for item in projects),
                    "jobs_error": sum(item["njobs_error"] for item in projects),
                    "total_credit": sum(item["user_total_credit"] for item in projects),
                },
            }
    except store.StoreError as exc:
        return jsonify({"online": False, "error": str(exc)}), 200
    except BoincAuthError as exc:
        return jsonify({"online": False, "error": str(exc)}), 200
    except (BoincError, OSError) as exc:
        return jsonify({"online": False, "error": str(exc)}), 200

    return jsonify(payload)


@app.route("/api/servers/<server_id>/control", methods=["POST"])
def control(server_id):
    server = store.find_server(server_id)
    if not server:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(force=True, silent=True) or {}
    op = data.get("op")
    project_url = (data.get("project_url") or "").strip()
    name = (data.get("name") or "").strip()

    try:
        password = store.server_password(server)
        with BoincRPC(server["host"], server["port"], password, timeout=10) as rpc:
            if op == "suspend_result":
                rpc.suspend_result(project_url, name)
            elif op == "resume_result":
                rpc.resume_result(project_url, name)
            elif op == "project_update":
                rpc.project_update(project_url)
            elif op == "project_suspend":
                rpc.project_suspend(project_url)
            elif op == "project_resume":
                rpc.project_resume(project_url)
            else:
                return jsonify({"error": "Unknown operation"}), 400
    except store.StoreError as exc:
        return jsonify({"error": str(exc)}), 400
    except (BoincError, OSError) as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8770))
    app.run(host="0.0.0.0", port=port)
