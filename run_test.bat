@echo off
rem Run pytest tests and exit with same return code
python -m pytest -q
exit /b %ERRORLEVEL%