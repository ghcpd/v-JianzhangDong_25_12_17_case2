# Security Audit and Fix for input.py

## Overview

This project contains the original vulnerable `input.py` backed up as `input_backup.py`, the secured version `input.py`, and various scripts for testing and deployment.

### Generated Files

- `input_backup.py`: Backup of the original vulnerable code.
- `input.py`: Secured version with fixes applied.
- `report.json`: Detailed report of vulnerabilities and fixes.
- `requirements.txt`: Python dependencies.
- `Dockerfile`: For containerized deployment.
- `setup.sh`: Setup script for Linux/macOS.
- `run_test.sh`: Test script for Linux/macOS.
- `run_test.bat`: Test script for Windows.
- `auto_test.py`: Automatic test runner that detects environment and runs tests.
- `test_security.py`: Security test script.
- `logs/test_run.log`: Log file for test results.

## Setup Instructions

### Linux/macOS

1. Run `./setup.sh` to install dependencies and set environment variables.
2. Edit `setup.sh` to set actual environment variables.

### Windows

1. Install Python and pip.
2. Run `pip install -r requirements.txt`.
3. Set environment variables manually.

### Docker

1. Build: `docker build -t secure-app .`
2. Run: `docker run -e PAYMENT_TOKEN=... -e MAIL_SERVER_KEY=... -e INTERNAL_AUTH=... -e SALT=... secure-app`

## Running Tests

### Manual

- Linux/macOS: `./run_test.sh input.py`
- Windows: `run_test.bat input.py`

### Automatic

Run `python auto_test.py` to automatically detect the environment and test both `input_backup.py` and `input.py`.

## Checking Logs

View `logs/test_run.log` for detailed test output. Each test run includes timestamp, file name, output, and final status (TEST PASSED or TEST FAILED).

- TEST PASSED: No vulnerabilities detected (exploits blocked).
- TEST FAILED: Vulnerabilities present (exploits succeeded).