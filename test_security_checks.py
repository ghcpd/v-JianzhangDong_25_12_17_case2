#!/usr/bin/env python3
"""Simple static checks that look for known-vulnerable patterns in a source file.
This is deliberately small and deterministic so tests can show a difference between
input_backup.py (expected to be vulnerable) and input.py (expected to be cleaned).
Exit code 0 means no vulnerable patterns found; non-zero means issue detected.
"""
import re
import sys

VULN_PATTERNS = [
    (r"PAYMENT_TOKEN\s*=\s*\"", "hardcoded payment token"),
    (r"MAIL_SERVER_KEY\s*=\s*\"", "hardcoded mail server key"),
    (r"INTERNAL_AUTH\s*=\s*\"", "hardcoded internal auth"),
    (r"hashlib\.md5", "use of md5 hash"),
    (r"WHERE id = '%s'", "string-formatted SQL (possible SQL injection)"),
    (r"requests\.post\([^,]*notify_url|requests\.post\(url", "unvalidated outbound request (possible SSRF)"),
    (r"subprocess\.Popen\([^)]*shell=\s*True", "shell=True usage (command injection)"),
    (r"open\([^)]*\)\s*as\s*f:\s*\n\s*\s*cfg\s*=\s*yaml\.safe_load", "unsanitized open + yaml.safe_load (path traversal / arbitrary file read)"),
    (r"app\.run\(debug=True\)", "debug server enabled in source"),
]


def check_file(path):
    data = open(path, "r", encoding="utf-8").read()
    findings = []
    for pat, desc in VULN_PATTERNS:
        if re.search(pat, data):
            findings.append((pat, desc))
    return findings


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: test_security_checks.py <file-to-check>")
        sys.exit(2)
    path = sys.argv[1]
    issues = check_file(path)
    if issues:
        print(f"{path}: VULNERABILITIES FOUND:")
        for p, d in issues:
            print(f" - {d} (pattern: {p})")
        sys.exit(1)
    else:
        print(f"{path}: OK - no vulnerable patterns detected")
        sys.exit(0)
