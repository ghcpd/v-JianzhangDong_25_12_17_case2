import os
import tempfile
import sqlite3
import importlib.machinery
import importlib.util
import sys
import json

import pytest

TARGET_FILE = os.environ.get("TARGET_FILE")
if not TARGET_FILE:
    pytest.skip("TARGET_FILE not set", allow_module_level=True)


def load_target_module(path):
    loader = importlib.machinery.SourceFileLoader("target_module", path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def prepare_env(tmpdir):
    db_path = os.path.join(tmpdir, "appdata.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("CREATE TABLE profiles (id INTEGER PRIMARY KEY, name TEXT, balance INTEGER);")
    c.execute("INSERT INTO profiles (id,name,balance) VALUES (1,'alice',1000);")
    conn.commit()
    conn.close()

    cfg_dir = os.path.join(tmpdir, "configs")
    os.makedirs(cfg_dir, exist_ok=True)
    with open(os.path.join(cfg_dir, "app.yml"), "w", encoding="utf-8") as f:
        f.write("name: test\n")

    export_dir = os.path.join(tmpdir, "exports")
    os.makedirs(export_dir, exist_ok=True)

    env = os.environ.copy()
    env.update({
        "DB_FILE": db_path,
        "CONFIG_DIR": cfg_dir,
        "EXPORT_DIR": export_dir,
        "PAYMENT_TOKEN": "test_tok",
        "INTERNAL_AUTH": "secret",
        "ADMIN_API_KEY": "adminkey",
    })
    return env


def test_security_behaviour(tmp_path, monkeypatch):
    env = prepare_env(str(tmp_path))
    # Set environment for this test run
    monkeypatch.setenv('DB_FILE', env['DB_FILE'])
    monkeypatch.setenv('CONFIG_DIR', env['CONFIG_DIR'])
    monkeypatch.setenv('EXPORT_DIR', env['EXPORT_DIR'])
    monkeypatch.setenv('PAYMENT_TOKEN', env['PAYMENT_TOKEN'])
    monkeypatch.setenv('INTERNAL_AUTH', env['INTERNAL_AUTH'])
    monkeypatch.setenv('ADMIN_API_KEY', env['ADMIN_API_KEY'])

    mod = load_target_module(TARGET_FILE)

    # 1) auth_user should produce an HMAC-SHA256 hex (length 64)
    t = mod.auth_user({"username": "alice"})
    assert isinstance(t, str)
    assert len(t) == 64, "Expected 64-char SHA256 hex token"

    # 2) query_profile should not be vulnerable to SQL injection
    res = mod.query_profile("1 OR 1=1")
    assert res == [], "SQL injection should be mitigated"

    # 3) transfer_funds should block unsafe notify URLs (e.g., localhost)
    r = mod.transfer_funds({"target": "alice", "amount": 10, "notify_url": "http://127.0.0.1:9999"})
    assert "error" in r

    # 4) update_records should prevent path traversal
    with pytest.raises(Exception):
        mod.update_records("../secrets.yml")

    # 5) export_data should reject malicious names
    with pytest.raises(Exception):
        mod.export_data("bad;name")

    # 6) export_data should succeed for safe name
    assert mod.export_data("safe_name") is True
    out_zip = os.path.join(env['EXPORT_DIR'], "safe_name.zip")
    assert os.path.exists(out_zip)
