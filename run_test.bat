@echo off
set BASE_URL=http://127.0.0.1:5000
REM Create DB
python - <<PY
import sqlite3
conn = sqlite3.connect('appdata.db')
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY, name TEXT, balance REAL)')
c.execute("INSERT OR REPLACE INTO profiles (id, name, balance) VALUES (1, 'Alice', 100.0)")
conn.commit()
conn.close()
print('DB ready')
PY

REM Start vulnerable app
start "backup" /B python input_backup.py
ping -n 3 127.0.0.1 >nul
python tests/test_vulnerabilities.py --base-url %BASE_URL% --expect-vulnerable
set RES1=%ERRORLEVEL%
REM Kill python processes (coarse)
taskkill /IM python.exe /F >nul 2>&1
ping -n 2 127.0.0.1 >nul

REM Start patched app
set ADMIN_API_KEY=testadminkey
set PAYMENT_TOKEN=test_payment_token
set INTERNAL_AUTH=test_internal_auth
start "patched" /B python input.py
ping -n 3 127.0.0.1 >nul
python tests/test_vulnerabilities.py --base-url %BASE_URL%
set RES2=%ERRORLEVEL%
REM Kill python processes
taskkill /IM python.exe /F >nul 2>&1

if %RES1%==0 if %RES2%==0 (
  echo TEST PASSED
  exit /b 0
) else (
  echo TEST FAILED
  exit /b 2
)
