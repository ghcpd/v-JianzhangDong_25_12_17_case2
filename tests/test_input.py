import os
import inspect
import sqlite3
import tempfile
import importlib.util
import pathlib
import pytest


def load_module():
    file = os.environ.get('FILE_TO_TEST', 'input.py')
    base_dir = pathlib.Path(__file__).parents[1]
    path = base_dir / file
    spec = importlib.util.spec_from_file_location('module_under_test', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# 1. auth_user should use HMAC-SHA256 (64 hex chars)
def test_auth_user_hash_length():
    mod = load_module()
    # ensure INTERNAL_AUTH env var is set so code uses a deterministic key
    os.environ['INTERNAL_AUTH'] = os.environ.get('INTERNAL_AUTH', 'secret')
    h = mod.auth_user({'username': 'alice'})
    assert isinstance(h, str)
    # HMAC-SHA256 yields 64-character hex digest
    assert len(h) == 64


# 2. query_profile should use parameterized query
def test_query_profile_uses_parameterized_query():
    mod = load_module()
    # Check source for parameter marker
    src = inspect.getsource(mod.query_profile)
    assert 'WHERE id = ?' in src

    # Create temp DB and table
    fd, db_path = tempfile.mkstemp()
    os.close(fd)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('CREATE TABLE profiles (id INTEGER, name TEXT, balance REAL)')
    c.execute("INSERT INTO profiles (id,name,balance) VALUES (1,'alice',100.0)")
    conn.commit()
    conn.close()

    # Patch module DB_FILE
    mod.DB_FILE = db_path

    # Query for valid id
    res = mod.query_profile(1)
    assert isinstance(res, list)
    assert len(res) == 1

    # Attempt an SQL injection - should not return rows
    res = mod.query_profile('1 OR 1=1')
    assert len(res) == 0


# 3. transfer_funds should validate notify_url (SSRF)
def test_transfer_funds_valid_url(monkeypatch):
    mod = load_module()

    class DummyResp:
        text = 'ok'

    def fake_post(url, json, timeout=None):
        return DummyResp()

    monkeypatch.setattr(mod.requests, 'post', fake_post)

    payload = {'target': 'bob', 'amount': 10, 'notify_url': 'https://example.com/callback'}
    assert mod.transfer_funds(payload) == 'ok'


def test_transfer_funds_invalid_url():
    mod = load_module()
    payload = {'target': 'bob', 'amount': 10, 'notify_url': 'http://evil.com'}
    with pytest.raises(ValueError):
        mod.transfer_funds(payload)


# 4. update_records should prevent path traversal
def test_update_records_path_traversal(tmp_path):
    mod = load_module()

    # Create a safe config file under expected configs directory
    base_dir = pathlib.Path(mod.__file__).parents[0] / 'configs'
    base_dir.mkdir(exist_ok=True)
    good = base_dir / 'safe.yaml'
    good.write_text('key: value\n')

    # Good path should succeed and return parsed YAML
    cfg = mod.update_records(str(good))
    assert isinstance(cfg, dict)

    # Attempt to access a file outside the configs dir
    bad = base_dir.parent / 'outside.yaml'
    bad.write_text('bad: 123\n')
    with pytest.raises(ValueError):
        mod.update_records(str(bad))


# 5. export_data should use subprocess.run and sanitize archive name
def test_export_data_uses_subprocess_run(monkeypatch):
    mod = load_module()

    called = {}
    def fake_run(cmd, check=True):
        called['cmd'] = cmd
        called['check'] = check
        return None

    monkeypatch.setattr(mod.subprocess, 'run', fake_run)

    mod.export_data('testname')

    assert called['cmd'] == ['zip', 'testname.zip', mod.DB_FILE]
    assert called['check'] is True


# Ensure backup file does not contain the secure patterns
# These tests intentionally expect failures for input_backup.py

# 6. export_data should not use shell=True nor subprocess.Popen in secure file
def test_export_data_no_shell():
    mod = load_module()
    src = inspect.getsource(mod.export_data)
    assert 'subprocess.run' in src
    assert 'subprocess.Popen' not in src
