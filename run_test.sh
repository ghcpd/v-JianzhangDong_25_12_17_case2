#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON=${PYTHON:-python3}

echo "Running security checks on input_backup.py (expected to FAIL)"
if ${PYTHON} test_security_checks.py input_backup.py; then
  echo "ERROR: input_backup.py unexpectedly passed checks"
  backup_ok=1
else
  echo "input_backup.py correctly flagged as vulnerable"
  backup_ok=0
fi

echo "Running security checks on input.py (expected to PASS)"
if ${PYTHON} test_security_checks.py input.py; then
  echo "input.py passed security checks"
  fixed_ok=1
else
  echo "ERROR: input.py still has vulnerabilities"
  fixed_ok=0
fi

# Overall success criteria: input_backup.py must be detected vulnerable (backup_ok==0) and input.py must pass (fixed_ok==1)
if [ "$backup_ok" -eq 0 ] && [ "$fixed_ok" -eq 1 ]; then
  echo "TEST PASSED"
  exit 0
else
  echo "TEST FAILED"
  exit 2
fi
