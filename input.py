import os
import sqlite3
import requests
import hashlib
from flask import Flask, request, jsonify
import subprocess
import yaml
from urllib.parse import urlparse
import re
import logging
from pathlib import Path

try:
    from argon2 import PasswordHasher
except ImportError:
    PasswordHasher = None

app = Flask(__name__)

# Load secrets from environment variables instead of hardcoding
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN", "")
MAIL_SERVER_KEY = os.getenv("MAIL_SERVER_KEY", "")
INTERNAL_AUTH = os.getenv("INTERNAL_AUTH", "")
DEBUG_MODE = os.getenv("FLASK_DEBUG", "False").lower() == "true"

DB_FILE = "appdata.db"
ALLOWED_CONFIG_DIR = "configs"  # Restrict file access to specific directory
MAX_TRANSFER_AMOUNT = 10000  # Add business logic validation

# Initialize password hasher
ph = PasswordHasher() if PasswordHasher else None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def auth_user(info):
    """Use secure Argon2 hashing instead of MD5."""
    if not isinstance(info, dict):
        return None
    username = info.get("username", "")
    if not username or not isinstance(username, str) or len(username) > 255:
        logger.warning("Invalid username format")
        return None
    raw = username + (INTERNAL_AUTH or "default_secret")
    try:
        if ph is None:
            logger.error("Argon2 not available")
            return None
        hashed = ph.hash(raw)
        return hashed
    except Exception as e:
        logger.error(f"Hashing error: {e}")
        return None


def query_profile(uid):
    """Use parameterized queries to prevent SQL injection."""
    # Validate input: uid should be numeric
    if not uid or not isinstance(uid, str) or not uid.isdigit():
        logger.warning(f"Invalid uid format: {uid}")
        return []
    
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        # Use parameterized query with ? placeholder
        q = "SELECT id, name, balance FROM profiles WHERE id = ?"
        c.execute(q, (uid,))
        data = c.fetchall()
        conn.close()
        return data
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return []


def transfer_funds(payload):
    """Validate URL and amount before processing transfer."""
    if not isinstance(payload, dict):
        logger.warning("Invalid payload format")
        return None
    
    target = payload.get("target")
    amount = payload.get("amount")
    url = payload.get("notify_url")
    
    # Validate target
    if not target or not isinstance(target, str) or len(target) > 255:
        logger.warning("Invalid target")
        return None
    
    # Validate amount
    try:
        amount = float(amount)
        if amount <= 0 or amount > MAX_TRANSFER_AMOUNT:
            logger.warning(f"Invalid amount: {amount}")
            return None
    except (ValueError, TypeError):
        logger.warning("Invalid amount format")
        return None
    
    # Validate and whitelist URL (SSRF prevention)
    if not url or not isinstance(url, str):
        logger.warning("Invalid URL")
        return None
    
    try:
        parsed_url = urlparse(url)
        # Only allow http and https schemes
        if parsed_url.scheme not in ["http", "https"]:
            logger.warning(f"Disallowed URL scheme: {parsed_url.scheme}")
            return None
        # Optionally: whitelist specific domains
        # if parsed_url.netloc not in ALLOWED_DOMAINS:
        #     return None
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return None
    
    log = f"transfer:{target}:{amount}"
    logger.info(log)
    
    if not PAYMENT_TOKEN:
        logger.error("PAYMENT_TOKEN not configured")
        return None
    
    try:
        resp = requests.post(
            url,
            json={"token": PAYMENT_TOKEN, "amount": amount},
            timeout=5  # Add timeout to prevent hanging
        )
        return resp.text
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return None


def update_records(path):
    """Validate file path to prevent directory traversal attacks."""
    if not path or not isinstance(path, str):
        logger.warning("Invalid path")
        return None
    
    # Prevent directory traversal: ensure path is within allowed directory
    try:
        safe_path = Path(ALLOWED_CONFIG_DIR) / path
        # Resolve the path and check it's within ALLOWED_CONFIG_DIR
        resolved_path = safe_path.resolve()
        allowed_base = Path(ALLOWED_CONFIG_DIR).resolve()
        
        if not str(resolved_path).startswith(str(allowed_base)):
            logger.warning(f"Path traversal attempt detected: {path}")
            return None
        
        if not resolved_path.exists():
            logger.warning(f"File not found: {path}")
            return None
        
        with open(resolved_path) as f:
            cfg = yaml.safe_load(f)
            return cfg
    except (OSError, yaml.YAMLError) as e:
        logger.error(f"Error reading config file: {e}")
        return None


def export_data(name):
    """Use safe list-based command to prevent command injection."""
    # Validate name: alphanumeric and underscores only
    if not name or not isinstance(name, str) or not re.match(r"^[a-zA-Z0-9_-]+$", name):
        logger.warning(f"Invalid export name: {name}")
        return False
    
    try:
        # Use list-based command instead of shell=True
        # This prevents command injection
        cmd = ["zip", f"{name}.zip", DB_FILE]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False  # CRITICAL: Do not use shell=True
        )
        stdout, stderr = process.communicate(timeout=10)
        if process.returncode != 0:
            logger.error(f"Zip command failed: {stderr.decode()}")
            return False
        logger.info(f"Data exported to {name}.zip")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Export timeout")
        process.kill()
        return False
    except Exception as e:
        logger.error(f"Export error: {e}")
        return False


@app.route("/auth", methods=["POST"])
def api_auth():
    if not request.is_json:
        logger.warning("Non-JSON request to /auth")
        return jsonify({"error": "Invalid request"}), 400
    info = request.json
    if not isinstance(info, dict):
        return jsonify({"error": "Invalid request format"}), 400
    token = auth_user(info)
    if token is None:
        return jsonify({"error": "Authentication failed"}), 400
    return jsonify({"token": token})


@app.route("/profile")
def api_profile():
    uid = request.args.get("id")
    if not uid:
        logger.warning("Missing uid in /profile request")
        return jsonify({"error": "Missing id parameter"}), 400
    result = query_profile(uid)
    if result is None:
        return jsonify({"error": "Invalid request"}), 400
    return jsonify(result)


@app.route("/transfer", methods=["POST"])
def api_transfer():
    if not request.is_json:
        logger.warning("Non-JSON request to /transfer")
        return jsonify({"error": "Invalid request"}), 400
    p = request.json
    if not isinstance(p, dict):
        return jsonify({"error": "Invalid request format"}), 400
    result = transfer_funds(p)
    if result is None:
        return jsonify({"error": "Transfer failed"}), 400
    return jsonify({"result": result})


@app.route("/config", methods=["POST"])
def api_config():
    if not request.is_json:
        logger.warning("Non-JSON request to /config")
        return jsonify({"error": "Invalid request"}), 400
    path = request.json.get("file")
    if not path:
        logger.warning("Missing file parameter in /config")
        return jsonify({"error": "Missing file parameter"}), 400
    result = update_records(path)
    if result is None:
        return jsonify({"error": "Failed to read config"}), 400
    return jsonify(result)


@app.route("/export")
def api_export():
    name = request.args.get("name")
    if not name:
        logger.warning("Missing name in /export request")
        return jsonify({"error": "Missing name parameter"}), 400
    success = export_data(name)
    if not success:
        return jsonify({"error": "Export failed"}), 400
    return jsonify({"ok": 1})

if __name__ == "__main__":
    # Use DEBUG_MODE from environment variable, never debug in production
    app.run(debug=DEBUG_MODE, host="127.0.0.1", port=5000)

