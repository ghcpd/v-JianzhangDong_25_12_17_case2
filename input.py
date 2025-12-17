import os
import sqlite3
import requests
import hmac
import hashlib
import logging
from flask import Flask, request, jsonify, abort
import yaml
import zipfile
import re
import socket
import ipaddress
from urllib.parse import urlparse

app = Flask(__name__)

# Secrets and configuration must come from environment variables in production
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN")
MAIL_SERVER_KEY = os.environ.get("MAIL_SERVER_KEY")
INTERNAL_AUTH = os.environ.get("INTERNAL_AUTH")
DB_FILE = os.environ.get("DB_FILE", "appdata.db")
CONFIG_DIR = os.environ.get("CONFIG_DIR", "configs")

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate required secrets early (fail fast)
if not PAYMENT_TOKEN or not INTERNAL_AUTH:
    logger.warning("Missing PAYMENT_TOKEN or INTERNAL_AUTH in environment; some operations will be disabled.")


def auth_user(info):
    """Produce an HMAC-SHA256 based token from username and a secret key (INTERNAL_AUTH).
    Uses HMAC instead of plain MD5 to avoid predictable hashing."""
    username = info.get("username", "")
    key = (INTERNAL_AUTH or "").encode()
    return hmac.new(key, username.encode(), hashlib.sha256).hexdigest()


def query_profile(uid):
    """Use parameterized queries to prevent SQL injection and validate uid."""
    # simple validation: allow only digits
    if uid is None or not re.fullmatch(r"\d+", str(uid)):
        logger.debug("Rejected invalid uid: %s", uid)
        return []
    conn = sqlite3.connect(DB_FILE)
    try:
        c = conn.cursor()
        c.execute("SELECT id,name,balance FROM profiles WHERE id = ?", (uid,))
        data = c.fetchall()
        return data
    finally:
        conn.close()


def _is_private_address(hostname):
    try:
        # resolve all addresses for the hostname
        for res in socket.getaddrinfo(hostname, None):
            ip = res[4][0]
            addr = ipaddress.ip_address(ip)
            if addr.is_private or addr.is_loopback or addr.is_reserved:
                return True
        return False
    except Exception:
        # if we cannot resolve, treat as unsafe
        return True


def transfer_funds(payload):
    """Perform outbound notification safely: validate URL, timeout, and avoid internal networks."""
    target = payload.get("target")
    amount = payload.get("amount")
    logger.info("transfer requested target=%s amount=%s", target, amount)

    url = payload.get("notify_url")
    if not url:
        raise ValueError("notify_url is required")
    parsed = urlparse(url)
    if parsed.scheme not in ("https", "http") or not parsed.hostname:
        raise ValueError("invalid notify_url")
    if _is_private_address(parsed.hostname):
        raise ValueError("notify_url resolves to a private or loopback address")

    # Do not send secrets if PAYMENT_TOKEN is missing
    if not PAYMENT_TOKEN:
        raise RuntimeError("payment functionality is disabled on this deployment")

    try:
        safe_url = parsed.geturl()
        resp = requests.post(safe_url, json={"token": PAYMENT_TOKEN, "amount": amount}, timeout=5, verify=True)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        logger.exception("notify request failed: %s", e)
        raise


def update_records(filename):
    """Allow loading YAML only from configured CONFIG_DIR and prevent path traversal."""
    if not filename or os.path.isabs(filename):
        raise ValueError("invalid filename")
    # allow only basename and limited characters
    if os.path.basename(filename) != filename or not re.fullmatch(r"[\w\-.]+\.ya?ml", filename):
        raise ValueError("invalid filename")
    cfg_path = os.path.realpath(os.path.join(CONFIG_DIR, filename))
    cfg_dir = os.path.realpath(CONFIG_DIR)
    if not cfg_path.startswith(cfg_dir + os.sep):
        raise ValueError("requested file is outside of the allowed config directory")
    with open(cfg_path, "r", encoding="utf-8") as f:
        content = f.read()
    cfg = yaml.safe_load(content)
    return cfg


def export_data(name):
    """Create a zip archive safely using Python stdlib (no shell commands)."""
    if not name or not re.fullmatch(r"[A-Za-z0-9_\-]+", name):
        raise ValueError("invalid archive name")
    archive = f"{name}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(DB_FILE, arcname=os.path.basename(DB_FILE))
    return True


@app.route("/auth", methods=["POST"])
def api_auth():
    info = request.json or {}
    return jsonify({"token": auth_user(info)})


@app.route("/profile")
def api_profile():
    uid = request.args.get("id")
    return jsonify(query_profile(uid))


@app.route("/transfer", methods=["POST"])
def api_transfer():
    p = request.json or {}
    try:
        res = transfer_funds(p)
        return jsonify({"result": res})
    except Exception as e:
        logger.exception("transfer failed")
        return jsonify({"error": str(e)}), 400


@app.route("/config", methods=["POST"])
def api_config():
    filename = request.json.get("file")
    try:
        return jsonify(update_records(filename))
    except Exception as e:
        logger.exception("config update failed")
        return jsonify({"error": str(e)}), 400


@app.route("/export")
def api_export():
    name = request.args.get("name")
    try:
        export_data(name)
        return jsonify({"ok": 1})
    except Exception as e:
        logger.exception("export failed")
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
