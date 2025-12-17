@echo off
setlocal enabledelayedexpansion

echo.
echo ==========================================
echo Running Security Tests (Windows)
echo ==========================================
echo.

if not exist "logs" mkdir logs

set FLASK_ENV=testing
set FLASK_DEBUG=False
set PAYMENT_TOKEN=test_token_12345
set MAIL_SERVER_KEY=test_mail_key_67890
set INTERNAL_AUTH=test_auth_abcde

set TEST_LOG=logs\test_run.log

echo Test log will be saved to: !TEST_LOG!
echo.

python test_security_windows.py > "!TEST_LOG!" 2>&1
set TEST_RESULT=!ERRORLEVEL!

python test_security_windows.py

echo.
echo ==========================================
if !TEST_RESULT! equ 0 (
    echo TEST PASSED
    echo TEST PASSED >> "!TEST_LOG!"
) else (
    echo TEST FAILED
    echo TEST FAILED >> "!TEST_LOG!"
)
echo ==========================================

for /f "tokens=2-4 delims=/ " %%%%a in ('date /t') do (set mydate=%%%%c-%%%%a-%%%%b)
for /f "tokens=1-2 delims=/:" %%%%a in ('time /t') do (set mytime=%%%%a:%%%%b)
echo Timestamp: !mydate! !mytime! >> "!TEST_LOG!"

exit /b !TEST_RESULT!
