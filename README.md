# Flask Security Audit and Remediation

## Overview

This directory contains a comprehensive security audit and remediation package for a Flask application. The original code (`input_backup.py`) contained **8 critical and high-severity vulnerabilities** that have been fixed in the secure version (`input.py`).

## Files and Purpose

### Core Application Files
- **`input_backup.py`** - Original vulnerable version for reference and testing comparison
- **`input.py`** - Secured version with all vulnerabilities fixed
- **`report.json`** - Detailed vulnerability report with line numbers, explanations, and fixes

### Setup and Configuration
- **`requirements.txt`** - Python package dependencies
- **`Dockerfile`** - Docker container configuration for production deployment
- **`setup.sh`** - Environment setup script for Linux/macOS
- **`.env.example`** - Example environment variable configuration

### Testing and Validation
- **`run_test.sh`** - Test runner script for Linux/macOS
- **`run_test.bat`** - Test runner script for Windows
- **`auto_test.py`** - Automatic test execution with environment detection and logging
- **`logs/test_run.log`** - Test execution logs with timestamps and results

### Documentation
- **`README.md`** - This file

## Vulnerabilities Fixed

### Critical Severity (3)
1. **SQL Injection** (Line 26) - Parameterized queries with input validation
2. **Command Injection** (Line 47) - List-based subprocess with shell=False
3. **Hardcoded Secrets** (Lines 12-14) - Environment variable configuration

### High Severity (3)
4. **Server-Side Request Forgery (SSRF)** (Line 37) - URL scheme validation and timeout
5. **Path Traversal** (Line 42) - Directory restriction and path normalization
6. **Debug Mode Enabled** (Line 61) - Environment-controlled debug setting

### Medium Severity (2)
7. **Weak Cryptographic Hashing** (Line 21) - MD5 replaced with Argon2
8. **Missing Input Validation** (Lines 54-75) - Type checking and format validation

See `report.json` for detailed explanations of each fix.

## Quick Start

### Linux/macOS

```bash
# 1. Setup environment
bash setup.sh

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run tests
bash run_test.sh

# 4. Run automatic tests with environment detection
python auto_test.py

# 5. Run the application
python input.py
```

### Windows

```powershell
# 1. Install dependencies (manual setup)
pip install -r requirements.txt

# 2. Set environment variables
$env:PAYMENT_TOKEN = "your_token_here"
$env:MAIL_SERVER_KEY = "your_key_here"
$env:INTERNAL_AUTH = "your_auth_here"
$env:FLASK_DEBUG = "False"

# 3. Run tests
run_test.bat

# 4. Run automatic tests with environment detection
python auto_test.py

# 5. Run the application
python input.py
```

### Docker

```bash
# 1. Build Docker image
docker build -t flask-secure-app .

# 2. Set environment variables in docker-compose.yml or use -e flag
docker run -e PAYMENT_TOKEN="token" \
           -e MAIL_SERVER_KEY="key" \
           -e INTERNAL_AUTH="auth" \
           -e FLASK_DEBUG="False" \
           -p 5000:5000 \
           flask-secure-app

# 3. Check health
curl http://localhost:5000/
```

## Environment Variables

Required environment variables (must be set before running):

```bash
export PAYMENT_TOKEN="your_production_payment_token"
export MAIL_SERVER_KEY="your_mail_server_key"
export INTERNAL_AUTH="your_internal_auth_secret"
export FLASK_DEBUG="False"  # Never set to True in production
export FLASK_ENV="production"  # Use 'production' or 'testing'
```

## Running Tests

### Linux/macOS

```bash
# Simple test execution
bash run_test.sh

# Automatic environment detection and testing
python auto_test.py

# Check test results
tail -f logs/test_run.log
```

### Windows

```batch
# Simple test execution
run_test.bat

# Automatic environment detection and testing
python auto_test.py

# Check test results
type logs\test_run.log
```

### Docker

Tests can be run inside the container:

```bash
docker run -it --rm \
  -e PAYMENT_TOKEN="test_token" \
  -e MAIL_SERVER_KEY="test_key" \
  -e INTERNAL_AUTH="test_auth" \
  flask-secure-app \
  python auto_test.py
```

## Test Execution Details

### auto_test.py Features

1. **Environment Detection**: Automatically detects Windows, Linux, or Docker
2. **Sequential Testing**: Tests input_backup.py (vulnerable) then input.py (secure)
3. **Comprehensive Logging**: 
   - Timestamps for all operations
   - Separate logging for each file tested
   - Output saved to `logs/test_run.log`
4. **Exit Code Handling**: 
   - Exit code 0: All tests passed
   - Exit code 1: Tests failed
5. **Status Line**: Final log entry shows "TEST PASSED" or "TEST FAILED"

### Test Suite Coverage

The tests validate the following security fixes:

- **SQL Injection Prevention**: Confirms parameterized queries work
- **Command Injection Prevention**: Validates input filtering for file names
- **Weak Hashing Prevention**: Checks for Argon2 hash format
- **Hardcoded Secrets Prevention**: Scans code for exposed credentials
- **Debug Mode Configuration**: Verifies environment-based control

### Interpreting Test Results

Check the test log file:

```bash
# View entire log
cat logs/test_run.log

# View final status
tail -1 logs/test_run.log

# Search for failures
grep "FAIL\|ERROR" logs/test_run.log
```

Expected output:
```
========================================
TEST PASSED
========================================
Timestamp: 2024-12-17 10:30:45
Status: TEST PASSED
```

## Security Improvements Summary

### Before (input_backup.py)
- SQL queries with string formatting (injection vulnerability)
- Subprocess with shell=True (command injection vulnerability)
- Hardcoded API tokens and secrets in code
- MD5 hashing for credentials
- No input validation on endpoints
- Debug mode always enabled

### After (input.py)
- Parameterized SQL queries with input validation
- List-based subprocess with shell=False and timeout
- Secrets loaded from environment variables
- Argon2 password hashing
- Comprehensive input validation on all endpoints
- Debug mode controlled by environment variable
- Structured logging for security events
- URL validation for SSRF prevention
- Directory restrictions for path traversal prevention

## Configuration Files

### .env Example
Create a `.env` file (or set environment variables):

```bash
# Security Tokens
PAYMENT_TOKEN=sk_live_abc123def456
MAIL_SERVER_KEY=mk_live_xyz789
INTERNAL_AUTH=auth_secret_key_12345

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=False

# Application Settings
MAX_TRANSFER_AMOUNT=10000
ALLOWED_CONFIG_DIR=configs
```

### Docker Compose Example

```yaml
version: '3'
services:
  flask-app:
    build: .
    ports:
      - "5000:5000"
    environment:
      PAYMENT_TOKEN: ${PAYMENT_TOKEN}
      MAIL_SERVER_KEY: ${MAIL_SERVER_KEY}
      INTERNAL_AUTH: ${INTERNAL_AUTH}
      FLASK_ENV: production
      FLASK_DEBUG: "False"
    volumes:
      - ./logs:/app/logs
      - ./configs:/app/configs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Deployment Checklist

Before deploying to production:

- [ ] Set all required environment variables
- [ ] Run test suite and verify "TEST PASSED"
- [ ] Check log file in `logs/test_run.log`
- [ ] Disable debug mode (FLASK_DEBUG=False)
- [ ] Use HTTPS in production
- [ ] Implement rate limiting
- [ ] Add authentication to endpoints
- [ ] Configure CORS appropriately
- [ ] Set up monitoring and alerting
- [ ] Review and update database credentials
- [ ] Enable SQL encryption at rest
- [ ] Implement request logging and audit trails

## Troubleshooting

### Test Script Not Found
```bash
# Linux/macOS: Check permissions
chmod +x run_test.sh

# Ensure you're in the correct directory
pwd
ls -la run_test.sh
```

### Import Errors
```bash
# Install missing packages
pip install -r requirements.txt

# Or on macOS with Python 3:
pip3 install -r requirements.txt
```

### Permission Denied on Docker
```bash
# Build with proper permissions
docker build --build-arg UID=$(id -u) -t flask-secure-app .
```

### Port Already in Use
```bash
# Change the port in input.py or run on different port
python input.py --port 5001

# Or stop the service using port 5000
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows
```

## Security Considerations

### Development
- Use FLASK_DEBUG=False even in development
- Generate unique secrets for each environment
- Use HTTPS for all communications
- Implement authentication before endpoints
- Add rate limiting and CORS protection

### Production
- Secrets must be in environment variables or secure vaults
- Use a production WSGI server (Gunicorn, uWSGI)
- Deploy behind a reverse proxy (Nginx, Apache)
- Enable TLS/SSL for all connections
- Implement DDoS protection
- Monitor and log all security events
- Regular security audits and penetration testing
- Keep dependencies updated

## Support and Documentation

### API Endpoints (after adding authentication)

```bash
# Health check (example)
curl http://localhost:5000/

# Authentication
curl -X POST http://localhost:5000/auth \
  -H "Content-Type: application/json" \
  -d '{"username": "user"}'

# Profile (requires id parameter)
curl "http://localhost:5000/profile?id=1"

# Config update
curl -X POST http://localhost:5000/config \
  -H "Content-Type: application/json" \
  -d '{"file": "test_config.yaml"}'

# Data export
curl "http://localhost:5000/export?name=backup"

# Fund transfer
curl -X POST http://localhost:5000/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "target": "account_123",
    "amount": 100,
    "notify_url": "https://webhook.example.com/callback"
  }'
```

## Report Details

For a complete vulnerability assessment, refer to `report.json` which includes:
- Vulnerability ID
- File and line numbers
- Vulnerability type and severity
- Original vulnerable code
- Updated secure code
- Detailed fix explanation

```bash
# View the report
python -m json.tool report.json | less

# Or pretty print it
cat report.json | python -m json.tool
```

## Version Information

- **Python**: 3.8+
- **Flask**: 2.3.0
- **argon2-cffi**: 21.3.0
- **requests**: 2.31.0

## License and Usage

This security audit and remediation package is provided for educational and remediation purposes. Use in accordance with your organization's policies and applicable laws.

## Contact

For questions about the security audit or remediation process, please refer to the detailed explanations in `report.json`.
