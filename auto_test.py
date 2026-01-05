#!/usr/bin/env python3
import os
import subprocess
import sys
import time
import platform
from datetime import datetime

LOG_FILE = os.path.join('logs', 'test_run.log')
BASE_URL = 'http://127.0.0.1:5000'
PY = sys.executable

os.makedirs('logs', exist_ok=True)


def ts():
    return datetime.utcnow().isoformat() + 'Z'


def write_log(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(msg + '\n')
    print(msg)


import signal

def run_test_for(app_file, expect_vulnerable, env=None):
    env = env or os.environ.copy()
    write_log(f"[{ts()}] Starting app {app_file}")
    # Start process in its own process group so it can be terminated reliably
    if platform.system() == 'Windows':
        proc = subprocess.Popen([PY, app_file], env=env, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        proc = subprocess.Popen([PY, app_file], env=env, preexec_fn=os.setsid)
    time.sleep(2)
    write_log(f"[{ts()}] Running vulnerability tests against {app_file} (expect_vulnerable={expect_vulnerable})")
    cmd = [PY, 'tests/test_vulnerabilities.py', '--base-url', BASE_URL]
    if expect_vulnerable:
        cmd.append('--expect-vulnerable')
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out, _ = p.communicate(timeout=30)
    write_log(f"[{ts()}] Output for {app_file}:\n{out}")
    result = (p.returncode == 0)
    write_log(f"[{ts()}] Result for {app_file}: {'PASS' if result else 'FAIL'} (exit {p.returncode})")
    # terminate process group
    try:
        if platform.system() == 'Windows':
            proc.send_signal(signal.CTRL_BREAK_EVENT)
            proc.kill()
        else:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        try:
            proc.terminate()
        except Exception:
            proc.kill()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
    return result


if __name__ == '__main__':
    overall_ok = True
    write_log(f"[{ts()}] AUTO TEST START")

    # Prepare DB and configs
    write_log(f"[{ts()}] Preparing test DB and configs")
    subprocess.check_call([PY, '-c', "import sqlite3; conn=sqlite3.connect('appdata.db'); c=conn.cursor(); c.execute('CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY, name TEXT, balance REAL)'); c.execute(\"INSERT OR REPLACE INTO profiles (id, name, balance) VALUES (1, 'Alice', 100.0)\"); conn.commit(); conn.close()"])
    os.makedirs('configs', exist_ok=True)
    with open(os.path.join('configs', 'sample.yaml'), 'w') as f:
        f.write('app:\n  name: secure-app\n')

    # Run vulnerable backup app tests
    ok_backup = run_test_for('input_backup.py', expect_vulnerable=True)
    overall_ok = overall_ok and ok_backup

    # Run patched app tests with required env vars
    env = os.environ.copy()
    env.update({
        'ADMIN_API_KEY': 'testadminkey',
        'PAYMENT_TOKEN': 'test_payment_token',
        'INTERNAL_AUTH': 'test_internal_auth',
        'CONFIG_DIR': os.path.abspath('configs')
    })
    ok_patched = run_test_for('input.py', expect_vulnerable=False, env=env)
    overall_ok = overall_ok and ok_patched

    final_status = 'TEST PASSED' if overall_ok else 'TEST FAILED'
    write_log(f"[{ts()}] {final_status}")
    sys.exit(0 if overall_ok else 2)
