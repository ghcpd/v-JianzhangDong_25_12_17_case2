@echo off
if "%TARGET_FILE%"=="" (
  echo TARGET_FILE not set
  exit /b 2
)
set TARGET_FILE=%TARGET_FILE%
python -m pytest tests\test_security.py -q
exit /b %ERRORLEVEL%
