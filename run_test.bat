@echo off
set PYTHON=python

echo Running security checks on input_backup.py (expected to FAIL)
%PYTHON% test_security_checks.py input_backup.py
if %ERRORLEVEL%==0 (
  echo ERROR: input_backup.py unexpectedly passed checks
  set backup_ok=1
) else (
  echo input_backup.py correctly flagged as vulnerable
  set backup_ok=0
)

echo Running security checks on input.py (expected to PASS)
%PYTHON% test_security_checks.py input.py
if %ERRORLEVEL%==0 (
  echo input.py passed security checks
  set fixed_ok=1
) else (
  echo ERROR: input.py still has vulnerabilities
  set fixed_ok=0
)

rem check overall
if "%backup_ok%"=="0" if "%fixed_ok%"=="1" (
  echo TEST PASSED
  exit /b 0
) else (
  echo TEST FAILED
  exit /b 2
)
