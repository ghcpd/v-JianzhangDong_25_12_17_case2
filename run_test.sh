#!/usr/bin/env bash
set -e
BASE_URL=http://127.0.0.1:5000
PYTHON=${PYTHON:-python}

# Ensure test DB and config
$PYTHON - <<'PY'
import sqlite3
conn = sqlite3.connect('appdata.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY, name TEXT, balance REAL)')
c.execute("INSERT OR REPLACE INTO profiles (id, name, balance) VALUES (1, 'Alice', 100.0)")
conn.commit()
conn.close()
print('DB ready')
PY

# Run vulnerable (backup) app
echo "Starting vulnerable app (input_backup.py)"
$PYTHON input_backup.py &
BPID=$!
sleep 2

echo "Running vulnerability checks against backup (expect vulnerable)"
set +e
$PYTHON tests/test_vulnerabilities.py --base-url $BASE_URL --expect-vulnerable
RES1=$?
set -e
kill $BPID || true
sleep 1

# Run patched (fixed) app
echo "Starting patched app (input.py)"
# set required environment variables for patched app
export ADMIN_API_KEY=testadminkey
export PAYMENT_TOKEN=test_payment_token
export INTERNAL_AUTH=test_internal_auth
export CONFIG_DIR=$(pwd)/configs
$PYTHON input.py &
PPID=$!
sleep 2

echo "Running vulnerability checks against patched app (expect secure)"
set +e
$PYTHON tests/test_vulnerabilities.py --base-url $BASE_URL
RES2=$?
set -e
kill $PPID || true
sleep 1

# Determine results
if [ "$RES1" -eq 0 ] && [ "$RES2" -eq 0 ]; then
  echo "TEST PASSED"
  exit 0
else
  echo "TEST FAILED"
  exit 2
fi
