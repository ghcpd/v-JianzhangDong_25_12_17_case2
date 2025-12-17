import os
import re
import sqlite3
import requests
import hashlib
import hmac
import logging
import zipfile
import io
from urllib.parse import urlparse
import socket
import ipaddress
from functools import wraps
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

# Configuration loaded from environment (no hardcoded secrets)
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.getenv("MAIL_SERVER_KEY")
INTERNAL_AUTH = os.getenv("INTERNAL_AUTH")
DB_FILE = os.getenv("DB_FILE", "appdata.db")
CONFIG_DIR = os.getenv("CONFIG_DIR", "./configs")
EXPORT_DIR = os.getenv("EXPORT_DIR", "./exports")
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helpers
name_re = re.compile(r"^[\w\-]+$")


def require_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = request.headers.get("X-API-KEY")
        if not ADMIN_API_KEY:
            logger.warning("ADMIN_API_KEY not configured; denying access")
            return jsonify({"error": "server_misconfigured"}), 503
        if not key or key != ADMIN_API_KEY:
            return jsonify({"error": "unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper


def auth_user(info):
    """Create a secure HMAC-SHA256 token for username using server secret."""
    username = info.get("username", "")
    if not INTERNAL_AUTH:
        raise RuntimeError("INTERNAL_AUTH not configured")
    token = hmac.new(INTERNAL_AUTH.encode(), username.encode(), hashlib.sha256).hexdigest()
    return token


def query_profile(uid):
    """Query the SQLite DB using parameterized queries to prevent SQL Injection."""
    if uid is None:
        return []
    if not str(uid).isdigit():
        logger.warning("Invalid profile id requested: %s", uid)
        return []
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        c.execute("SELECT id,name,balance FROM profiles WHERE id = ?", (uid,))
        data = c.fetchall()
    finally:
        conn.close()
    return data


def _is_safe_url(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname
        if not host:
            return False
        # Resolve host to IP and disallow private/local addresses
        ip = socket.gethostbyname(host)
        addr = ipaddress.ip_address(ip)
        if addr.is_private or addr.is_loopback or addr.is_reserved:
            return False
        return True
    except Exception:
        return False


def transfer_funds(payload):
    target = payload.get("target")
    amount = payload.get("amount")
    url = payload.get("notify_url")
    logger.info("Initiating transfer to %s amount %s", target, amount)

    if url is None or not _is_safe_url(url):
        logger.warning("Blocked unsafe notify URL: %s", url)
        return {"error": "unsafe_notify_url"}

    if not PAYMENT_TOKEN:
        logger.error("PAYMENT_TOKEN not configured")
        return {"error": "server_misconfigured"}

    headers = {"Authorization": f"Bearer {PAYMENT_TOKEN}"}
    try:
        resp = requests.post(url, json={"amount": amount}, headers=headers, timeout=5)
        resp.raise_for_status()
        return {"status": "ok", "response": resp.text}
    except Exception as e:
        logger.exception("Error notifying payment endpoint")
        return {"error": str(e)}


def update_records(path):
    """Load configuration files only from a designated config directory."""
    if not path:
        raise ValueError("missing_file_path")

    safe_base = os.path.realpath(CONFIG_DIR)
    candidate = os.path.realpath(os.path.join(CONFIG_DIR, path))
    if not candidate.startswith(safe_base):
        raise ValueError("invalid_config_path")

    with open(candidate, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


def export_data(name):
    """Create a zip archive in a safe export directory without using shell commands."""
    if not name or not name_re.match(name):
        raise ValueError("invalid_export_name")

    os.makedirs(EXPORT_DIR, exist_ok=True)
    out_path = os.path.join(EXPORT_DIR, f"{name}.zip")
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DB_FILE, arcname=os.path.basename(DB_FILE))
    logger.info("Export created at %s", out_path)
    return True


@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.json or {}
    try:
        token = auth_user(info)
        return jsonify({"token": token})
    except Exception as e:
        logger.exception("Auth error")
        return jsonify({"error": str(e)}), 500


@app.route("/profile")
@require_api_key
def api_profile():
    uid = request.args.get("id")
    return jsonify(query_profile(uid))


@app.route("/transfer", methods=["POST"])
@require_api_key
def api_transfer():
    p = request.json or {}
    return jsonify(transfer_funds(p))


@app.route("/config", methods=["POST"])
@require_api_key
def api_config():
    path = request.json.get("file")
    try:
        return jsonify(update_records(path))
    except Exception as e:
        logger.exception("Config update error")
        return jsonify({"error": str(e)}), 400


@app.route("/export")
@require_api_key
def api_export():
    name = request.args.get("name")
    try:
        export_data(name)
        return jsonify({"ok": 1})
    except Exception as e:
        logger.exception("Export error")
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", debug=debug_mode)

