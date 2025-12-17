#!/usr/bin/env bash
set -e
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# Create configs dir and a sample config
mkdir -p configs
cat > configs/sample.yaml <<'YAML'
app:
  name: secure-app
YAML
# Create a sample database for tests
python - <<'PY'
import sqlite3
conn = sqlite3.connect('appdata.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY, name TEXT, balance REAL)')
c.execute("INSERT OR REPLACE INTO profiles (id, name, balance) VALUES (1, 'Alice', 100.0)")
conn.commit()
conn.close()
print('Sample DB created')
PY

echo "Setup complete. Set environment variables PAYMENT_TOKEN, INTERNAL_AUTH, ADMIN_API_KEY before running the app in production."
