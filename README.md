# Security audit and fixes for input.py

Overview
- input_backup.py: original file (unchanged) saved as backup for comparison and testing.
- input.py: secured/updated source with fixes for SQLi, SSRF, command injection, path traversal, hardcoded secrets, and insecure debug mode.
- report.json: structured report listing vulnerabilities, affected lines, and fixes applied.
- requirements.txt: Python dependencies (Flask, requests, PyYAML).
- Dockerfile: simple image to run the app.
- setup.sh: installs dependencies on Linux/macOS.
- run_test.sh / run_test.bat: platform test wrappers that run `test_security_checks.py` and assert expected behavior (backup should fail checks; fixed file should pass).
- test_security_checks.py: deterministic static checks that look for vulnerable patterns in a single file.
- auto_test.py: automatic test runner that detects environment, runs per-file tests and platform wrapper, and logs to `logs/test_run.log` with timestamps and a final `TEST PASSED` or `TEST FAILED` line.
- logs/: directory where `auto_test.py` writes `test_run.log`.
- report.json: a JSON report of vulnerabilities and fixes.

Setup
1. (Optional) Create a Python virtual environment:
   - python -m venv .venv
   - source .venv/bin/activate   (Linux/macOS)
   - .venv\Scripts\activate    (Windows)
2. Install dependencies:
   - Linux/macOS: `./setup.sh`
   - Windows: `pip install -r requirements.txt`
3. Provide required environment variables before running the app in production (do NOT put secrets in source):
   - PAYMENT_TOKEN, INTERNAL_AUTH are expected to be provided via environment variables.
   - (Optional) MAIL_SERVER_KEY, DB_FILE, CONFIG_DIR, FLASK_HOST, FLASK_PORT, FLASK_DEBUG

Running tests
- Linux/macOS:
  1. Make run_test.sh executable: `chmod +x run_test.sh`
  2. `./run_test.sh` (script prints TEST PASSED or TEST FAILED and sets exit code accordingly)
- Windows:
  1. `run_test.bat` (runs checks and prints TEST PASSED or TEST FAILED)
- Automatic runner:
  - `python auto_test.py` will detect the platform, run tests and append results to `logs/test_run.log`.

Interpreting logs
- `logs/test_run.log` contains timestamped entries for each test run and ends with a `TEST PASSED` or `TEST FAILED` line for quick inspection.

Notes
- The test tooling is intentionally conservative and static (pattern-based) to make CI deterministic without starting the webserver.
- Before deploying the fixed `input.py`, ensure required environment variables are set and run `auto_test.py` to verify the environment.
