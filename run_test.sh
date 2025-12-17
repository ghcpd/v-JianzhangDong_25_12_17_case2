#!/usr/bin/env bash
set -euo pipefail
if [ -z "${TARGET_FILE:-}" ]; then
  echo "TARGET_FILE not set"
  exit 2
fi
export TARGET_FILE
pytest -q tests/test_security.py
