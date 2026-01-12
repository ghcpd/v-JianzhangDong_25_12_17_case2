#!/usr/bin/env python3
"""Automatic test runner that detects environment and runs the appropriate test script(s),
logs outputs to logs/test_run.log with timestamps and final status lines.

It performs per-file tests for input_backup.py and input.py (using test_security_checks.py)
and also runs the platform wrapper (run_test.sh or run_test.bat) to produce an overall status.
"""
import os
import sys
import subprocess
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "test_run.log")

os.makedirs(LOG_DIR, exist_ok=True)


def now():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{now()} {msg}\n")


def run_cmd(cmd, shell=False):
    try:
        p = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr
    except Exception as e:
        return 2, str(e)


def run_per_file_tests(python_exe="python3"):
    results = {}
    for fname in ("input_backup.py", "input.py"):
        log(f"BEGIN TEST {fname}")
        rc, out = run_cmd([python_exe, "test_security_checks.py", fname])
        log(f"FILE={fname} RC={rc}")
        for line in out.strip().splitlines():
            log(f"OUTPUT {fname}: {line}")
        results[fname] = rc
        log(f"END TEST {fname}")
    return results


def run_platform_wrapper():
    # choose wrapper
    if os.name == "nt":
        cmd = ["cmd", "/c", "run_test.bat"]
        shell = False
    else:
        cmd = ["/bin/bash", "run_test.sh"]
        shell = False
    log("BEGIN PLATFORM WRAPPER: %s" % " ".join(cmd))
    rc, out = run_cmd(cmd, shell=shell)
    log(f"PLATFORM_WRAPPER_RC={rc}")
    for line in out.strip().splitlines():
        log(f"PLATFORM_OUTPUT: {line}")
    log("END PLATFORM WRAPPER")
    return rc, out


if __name__ == "__main__":
    log("AUTO_TEST START")
    py = os.environ.get("PYTHON", "python")
    per_file = run_per_file_tests(python_exe=py)

    # interpret per-file results: expect input_backup.py to be non-zero (vulnerable detected)
    # and input.py to be zero (clean)
    backup_ok = (per_file.get("input_backup.py", 1) != 0)
    fixed_ok = (per_file.get("input.py", 1) == 0)

    rc_wrapper, out_wrapper = run_platform_wrapper()

    overall_pass = backup_ok and fixed_ok and (rc_wrapper == 0)

    if overall_pass:
        log("TEST PASSED")
        print("TEST PASSED")
        sys.exit(0)
    else:
        log("TEST FAILED")
        print("TEST FAILED")
        sys.exit(2)
