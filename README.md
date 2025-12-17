# Security Audit & Hardening for `input.py`

This repository contains a small Flask app (`input.py`) that originally had several security issues. Below you will find the audit findings, fixes applied, and scripts to reproduce the environment and run tests.

## Files in this repo
- `input.py` – secured version (the one you should use).
- `input_backup.py` – a backup copy of the original, vulnerable code.
- `report.json` – structured report of issues and fixes that were applied.
- `requirements.txt` – Python deps required to run the app/tests.
- `Dockerfile` – simple container that installs deps and runs the tests (CI-friendly).
- `setup.sh` – install dependencies on a local Linux/Mac system.
- `run_test.sh` / `run_test.bat` – convenience scripts to run the test suite
  (pytest) on Linux/macOS and Windows.
- `auto_test.py` – test runner that detects the environment and runs both
  `input_backup.py` and `input.py` tests, logging results to `logs/test_run.log`.
- `tests/test_input.py` – unit tests that assert the secure behaviours and
  demonstrate expected failures when running the backup version.

## What I did (high-level)
1. **Audit**: Identified 6 issues (hardcoded secrets, MD5, SQLi, SSRF, path traversal, command injection).
2. **Applied fixes**: Replaced secrets with environment variables, used HMAC + SHA256, parameterized SQL, validated URLs, prevented path traversal, removed `shell=True` and sanitized inputs.
3. **Added tests**: Checking for secure behaviour and expected failures on vulnerable backup.
4. **Auto test runner**: `auto_test.py` runs tests for both the vulnerable and fixed version, with logs at `logs/test_run.log`.

## How to set up the environment (Linux/macOS)
```
# Install deps
./setup.sh

# Run unit tests
./run_test.sh
```

On Windows, run:
```
setup.bat (if provided) or pip install -r requirements.txt
run_test.bat
```

Alternatively you can run the container:
```
# build container
docker build -t audit-app .
# run tests inside container
docker run --rm audit-app
```

## How to run the automatic test runner
This script will run the tests against BOTH the vulnerable and secure files and log the results.
```
python auto_test.py
```
Check the logs in `logs/test_run.log` for detail.

## Notes
- `app.run` was changed to listen on `0.0.0.0` and `debug=False` for production safety.
- Secrets are expected as environment variables: `PAYMENT_TOKEN`, `MAIL_SERVER_KEY`, `INTERNAL_AUTH`.

If you want to inspect the changes, open `report.json`.
