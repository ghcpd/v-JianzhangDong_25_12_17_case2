import os
import sqlite3
import requests
import hashlib
import hmac
import logging
import time
import re
import zipfile
from urllib.parse import urlparse
from flask import Flask, request, jsonify, abort
import yaml

app = Flask(__name__)

# Load secrets from environment. Do NOT hardcode secrets in source.
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.environ.get("MAIL_SERVER_KEY")
INTERNAL_AUTH = os.environ.get("INTERNAL_AUTH")
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")

DB_FILE = os.environ.get("DB_FILE", "appdata.db")
CONFIG_DIR = os.environ.get("CONFIG_DIR", "configs")

# Basic logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple helper for HMAC-based token generation (secure over MD5)
def auth_user(info):
    username = info.get("username", "")
    if not username:
        raise ValueError("username required")
    if not INTERNAL_AUTH:
        raise RuntimeError("INTERNAL_AUTH not configured")
    # include timestamp to make token short-lived if desired
    ts = str(int(time.time()))
    msg = f"{username}:{ts}".encode()
    token = hmac.new(INTERNAL_AUTH.encode(), msg, digestmod=hashlib.sha256).hexdigest()
    return f"{token}:{ts}"


def query_profile(uid):
    # Validate input: accept only digits
    if uid is None or not re.fullmatch(r"\d+", uid):
        logger.warning("Invalid uid provided to query_profile")
        return []
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        c.execute("SELECT id, name, balance FROM profiles WHERE id = ?", (int(uid),))
        data = c.fetchall()
        return data
    finally:
        conn.close()


def is_safe_url(url):
    try:
        p = urlparse(url)
        if p.scheme not in ("http", "https") or not p.netloc:
            return False
        # optionally restrict to non-private IPs; for tests allow localhost
        return True
    except Exception:
        return False


def transfer_funds(payload):
    target = payload.get("target")
    amount = payload.get("amount")
    notify_url = payload.get("notify_url")

    if not target or not amount:
        raise ValueError("target and amount are required")
    # amount should be numeric
    try:
        amt = float(amount)
        if amt <= 0:
            raise ValueError("amount must be positive")
    except Exception:
        raise ValueError("invalid amount")

    logger.info("transfer request for target=%s amount=%s", target, "[REDACTED]")

    if not is_safe_url(notify_url):
        raise ValueError("invalid notify_url")

    if not PAYMENT_TOKEN:
        raise RuntimeError("PAYMENT_TOKEN not configured")

    # create a short signature instead of sending raw token
    signature = hmac.new(PAYMENT_TOKEN.encode(), f"{target}:{amount}".encode(), hashlib.sha256).hexdigest()

    try:
        resp = requests.post(notify_url, json={"signature": signature, "amount": amount}, timeout=5)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.exception("Failed to notify: %s", e)
        return {"error": "notification failed"}
    return {"status": "notified", "http_status": resp.status_code}


def update_records(filename):
    # restrict to CONFIG_DIR and prevent path traversal
    if not filename or os.path.basename(filename) != filename:
        raise ValueError("invalid filename")
    if not filename.endswith((".yaml", ".yml")):
        raise ValueError("unsupported file type")
    full_path = os.path.join(CONFIG_DIR, filename)
    if not os.path.commonpath([os.path.abspath(full_path), os.path.abspath(CONFIG_DIR)]) == os.path.abspath(CONFIG_DIR):
        raise ValueError("invalid path")
    with open(full_path) as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    # sanitize name: allow only letters, numbers, dash and underscore
    if not name or not re.fullmatch(r"[A-Za-z0-9_\-]+", name):
        name = "export"
    zip_name = f"{name}.zip"
    # create zip securely using Python's zipfile module
    with zipfile.ZipFile(zip_name, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DB_FILE, arcname=os.path.basename(DB_FILE))
    return zip_name


# Simple API key decorator for protecting sensitive endpoints
from functools import wraps

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-API-KEY")
        if not ADMIN_API_KEY or key != ADMIN_API_KEY:
            abort(401)
        return f(*args, **kwargs)
    return decorated


@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.json or {}
    try:
        token = auth_user(info)
    except Exception as e:
        logger.exception("auth failed: %s", e)
        return jsonify({"error": "auth failed"}), 400
    return jsonify({"token": token})


@app.route("/profile")
@require_api_key
def api_profile():
    uid = request.args.get("id")
    return jsonify(query_profile(uid))


@app.route("/transfer", methods=["POST"])
@require_api_key
def api_transfer():
    p = request.json or {}
    try:
        result = transfer_funds(p)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"result": result})


@app.route("/config", methods=["POST"])
@require_api_key
def api_config():
    filename = request.json.get("file")
    try:
        data = update_records(filename)
    except Exception as e:
        logger.exception("config update failed: %s", e)
        return jsonify({"error": "invalid request"}), 400
    return jsonify(data)


@app.route("/export")
@require_api_key
def api_export():
    name = request.args.get("name")
    try:
        zip_name = export_data(name)
    except Exception as e:
        logger.exception("export failed: %s", e)
        return jsonify({"error": "export failed"}), 400
    return jsonify({"ok": 1, "file": zip_name})


if __name__ == "__main__":
    debug_flag = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", debug=debug_flag)
