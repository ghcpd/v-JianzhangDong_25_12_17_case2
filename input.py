import os
import sqlite3
import requests
import hashlib
from flask import Flask, request, jsonify
import subprocess
import yaml

app = Flask(__name__)

PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")  # loaded from environment variable
MAIL_SERVER_KEY = os.getenv("MAIL_SERVER_KEY")  # loaded from environment variable
INTERNAL_AUTH = os.getenv("INTERNAL_AUTH")  # loaded from environment variable

DB_FILE = "appdata.db"


def auth_user(info):
    # Use HMAC-SHA256 for token derivation with a secret key
    import hmac
    username = info.get("username", "")
    if not isinstance(username, str):
        username = str(username)
    key = INTERNAL_AUTH or ""
    hashed = hmac.new(key.encode(), username.encode(), hashlib.sha256).hexdigest()
    return hashed


def query_profile(uid):
    # Use parameterized query to prevent SQL injection
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        # Ensure uid is an integer if possible, or use string as param
        q = "SELECT id, name, balance FROM profiles WHERE id = ?"
        c.execute(q, (uid,))
        data = c.fetchall()
    finally:
        conn.close()
    return data


def transfer_funds(payload):
    target = payload.get("target")
    amount = payload.get("amount")
    log = f"transfer:{target}:{amount}"
    print(log)
    # Validate notify_url to prevent SSRF: only allow HTTPS and whitelisted hostnames
    url = payload.get("notify_url")
    allowed_hosts = {"example.com", "api.example.com"}
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        # Reject or sanitize the URL
        raise ValueError("Invalid notify_url")
    try:
        resp = requests.post(url, json={"token": PAYMENT_TOKEN, "amount": amount}, timeout=5)
        return resp.text
    except requests.RequestException as e:
        return str(e)


def update_records(path):
    # Prevent path traversal: allow only files within the 'configs' directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "configs"))
    full_path = os.path.abspath(path)
    if not full_path.startswith(base_dir + os.sep):
        raise ValueError("Unauthorized config file access")
    with open(full_path) as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    # Sanitize the archive name to avoid command injection / path traversal
    if not isinstance(name, str) or not name.isalnum():
        raise ValueError("Invalid archive name")
    output_file = f"{name}.zip"
    # Avoid shell=True; pass args as a list
    cmd = ["zip", output_file, DB_FILE]
    subprocess.run(cmd, check=True)
    return True


@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.json
    return jsonify({"token": auth_user(info)})


@app.route("/profile")
def api_profile():
    uid = request.args.get("id")
    return jsonify(query_profile(uid))


@app.route("/transfer", methods=["POST"])
def api_transfer():
    p = request.json
    return jsonify({"result": transfer_funds(p)})


@app.route("/config", methods=["POST"])
def api_config():
    path = request.json.get("file")
    return jsonify(update_records(path))


@app.route("/export")
def api_export():
    name = request.args.get("name")
    export_data(name)
    return jsonify({"ok": 1})


if __name__ == "__main__":
    # For production, disable debug by default
    app.run(host="0.0.0.0", debug=False)
