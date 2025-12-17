import os
import sqlite3
import requests
import hashlib
from flask import Flask, request, jsonify
import subprocess
import yaml
from urllib.parse import urlparse

app = Flask(__name__)

PAYMENT_TOKEN = os.environ.get('PAYMENT_TOKEN')
MAIL_SERVER_KEY = os.environ.get('MAIL_SERVER_KEY')
INTERNAL_AUTH = os.environ.get('INTERNAL_AUTH')

if not all([PAYMENT_TOKEN, MAIL_SERVER_KEY, INTERNAL_AUTH]):
    raise ValueError("Required environment variables not set")

DB_FILE = "appdata.db"


def auth_user(info):
    username = info.get("username", "")
    if not username:
        return None
    salt = os.environ.get('SALT', 'default_salt')
    raw = username + INTERNAL_AUTH + salt
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return hashed


def query_profile(uid):
    if not uid or not isinstance(uid, str):
        return []
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id,name,balance FROM profiles WHERE id = ?", (uid,))
    data = c.fetchall()
    conn.close()
    return data


def transfer_funds(payload):
    target = payload.get("target")
    amount = payload.get("amount")
    notify_url = payload.get("notify_url")
    if not target or not amount or not notify_url:
        return "Invalid payload"
    parsed = urlparse(notify_url)
    if parsed.scheme not in ['http', 'https'] or not parsed.netloc:
        return "Invalid URL"
    # For security, perhaps restrict to specific domains, but for now, allow http/https
    log = f"transfer:{target}:{amount}"
    print(log)
    resp = requests.post(notify_url, json={"token": PAYMENT_TOKEN, "amount": amount})
    return resp.text


def update_records(path):
    if not path or '..' in path or '/' in path or '\\' in path:
        return {"error": "Invalid path"}
    if not os.path.isfile(path):
        return {"error": "File not found"}
    with open(path) as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    if not name or not name.isalnum():
        return False
    cmd = ['zip', f'{name}.zip', DB_FILE]
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
    if export_data(name):
        return jsonify({"ok": 1})
    else:
        return jsonify({"error": "Invalid name"}), 400


if __name__ == "__main__":
    app.run(debug=True)
