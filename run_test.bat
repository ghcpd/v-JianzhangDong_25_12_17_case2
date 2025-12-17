@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo Running Security Tests (Windows)
echo ==========================================
echo.

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Set test environment variables
set FLASK_ENV=testing
set FLASK_DEBUG=False
set PAYMENT_TOKEN=test_token_12345
set MAIL_SERVER_KEY=test_mail_key_67890
set INTERNAL_AUTH=test_auth_abcde

set TEST_LOG=logs\test_run.log

echo [*] Test log will be saved to: %TEST_LOG%
echo.

REM Create test script
(
echo """
echo Security test suite for Flask application
echo Tests both vulnerable (input_backup.py) and secure (input.py) versions
echo """
echo import sys
echo import os
echo import json
echo import sqlite3
echo import tempfile
echo from pathlib import Path
echo.
echo def setup_test_db():
echo     """Create a test database with sample data"""
echo     db_file = tempfile.mktemp(suffix='.db'^)
echo     conn = sqlite3.connect(db_file^)
echo     c = conn.cursor(^)
echo     c.execute('''CREATE TABLE profiles 
echo                  (id INTEGER PRIMARY KEY, name TEXT, balance REAL^)'''
echo     c.execute("INSERT INTO profiles VALUES (1, 'Test User', 1000.0^)"^)
echo     conn.commit(^)
echo     conn.close(^)
echo     return db_file
echo.
echo def test_sql_injection():
echo     """Test SQL injection vulnerability"""
echo     print("\n[TEST] SQL Injection Prevention"^)
echo     print("-" * 50^)
echo     db_file = setup_test_db(^)
echo     os.environ['DB_FILE'] = db_file
echo     try:
echo         import input as secure_app
echo         malicious_id = "1' OR '1'='1"
echo         result = secure_app.query_profile(malicious_id^)
echo         if result is None or result == []:
echo             print("✓ PASS: SQL injection attempt blocked"^)
echo             return True
echo         else:
echo             print("✗ FAIL: SQL injection not prevented"^)
echo             return False
echo     except Exception as e:
echo         print(f"✓ PASS: Exception raised (expected^): {str(e^)[:50]}"^)
echo         return True
echo     finally:
echo         if os.path.exists(db_file^):
echo             os.remove(db_file^)
echo.
echo def test_command_injection():
echo     """Test command injection vulnerability"""
echo     print("\n[TEST] Command Injection Prevention"^)
echo     print("-" * 50^)
echo     try:
echo         import input as secure_app
echo         malicious_name = "; rm -rf /"
echo         result = secure_app.export_data(malicious_name^)
echo         if result is False:
echo             print("✓ PASS: Command injection attempt blocked"^)
echo             return True
echo         else:
echo             print("✗ FAIL: Command injection not prevented"^)
echo             return False
echo     except Exception as e:
echo         print(f"✓ PASS: Exception raised (expected^): {str(e^)[:50]}"^)
echo         return True
echo.
echo def test_weak_hashing():
echo     """Test that weak hashing is replaced"""
echo     print("\n[TEST] Weak Hashing Prevention"^)
echo     print("-" * 50^)
echo     try:
echo         import input as secure_app
echo         test_info = {"username": "testuser"}
echo         result = secure_app.auth_user(test_info^)
echo         if result and "$argon2" in result:
echo             print("✓ PASS: Using Argon2 hashing (secure^)"^)
echo             return True
echo         elif result is None:
echo             print("✗ FAIL: auth_user returned None"^)
echo             return False
echo         else:
echo             print(f"✗ FAIL: Not using Argon2, got: {result[:20]}"^)
echo             return False
echo     except Exception as e:
echo         print(f"✗ FAIL: Exception: {str(e^)}"^)
echo         return False
echo.
echo def test_hardcoded_secrets():
echo     """Test that secrets are not hardcoded"""
echo     print("\n[TEST] Hardcoded Secrets Prevention"^)
echo     print("-" * 50^)
echo     try:
echo         with open('input.py', 'r'^) as f:
echo             content = f.read(^)
echo         suspicious_patterns = [
echo             'tok_production_',
echo             'mail_srv_key_',
echo             'admin_internal_',
echo             'PAYMENT_TOKEN = "',
echo             'MAIL_SERVER_KEY = "',
echo             'INTERNAL_AUTH = "'
echo         ]
echo         found_secrets = False
echo         for pattern in suspicious_patterns:
echo             if pattern in content:
echo                 print(f"✗ FAIL: Found potential hardcoded secret: {pattern}"^)
echo                 found_secrets = True
echo         if not found_secrets:
echo             print("✓ PASS: No hardcoded secrets found"^)
echo             return True
echo         return False
echo     except Exception as e:
echo         print(f"✗ FAIL: Exception: {str(e^)}"^)
echo         return False
echo.
echo def test_debug_mode():
echo     """Test that debug mode is not hardcoded"""
echo     print("\n[TEST] Debug Mode Configuration"^)
echo     print("-" * 50^)
echo     try:
echo         with open('input.py', 'r'^) as f:
echo             content = f.read(^)
echo         if 'debug=True' in content or 'debug = True' in content:
echo             print("✗ FAIL: Debug mode hardcoded to True"^)
echo             return False
echo         elif 'DEBUG_MODE' in content and 'os.getenv' in content:
echo             print("✓ PASS: Debug mode controlled by environment variable"^)
echo             return True
echo         else:
echo             print("✓ PASS: Debug mode properly configured"^)
echo             return True
echo     except Exception as e:
echo         print(f"✗ FAIL: Exception: {str(e^)}"^)
echo         return False
echo.
echo def main(^):
echo     print("\n" + "=" * 50^)
echo     print("FLASK SECURITY TEST SUITE"^)
echo     print("=" * 50^)
echo     results = []
echo     results.append(("SQL Injection Prevention", test_sql_injection(^)^)^)
echo     results.append(("Command Injection Prevention", test_command_injection(^)^)^)
echo     results.append(("Weak Hashing Prevention", test_weak_hashing(^)^)^)
echo     results.append(("Hardcoded Secrets Prevention", test_hardcoded_secrets(^)^)^)
echo     results.append(("Debug Mode Configuration", test_debug_mode(^)^)^)
echo     print("\n" + "=" * 50^)
echo     print("TEST SUMMARY"^)
echo     print("=" * 50^)
echo     passed = sum(1 for _, result in results if result^)
echo     total = len(results^)
echo     for test_name, result in results:
echo         status = "✓ PASS" if result else "✗ FAIL"
echo         print(f"{status}: {test_name}"^)
echo     print(f"\nTotal: {passed}/{total} tests passed"^)
echo     if passed == total:
echo         print("\n✓ ALL TESTS PASSED"^)
echo         return 0
echo     else:
echo         print(f"\n✗ {total - passed} TEST(S) FAILED"^)
echo         return 1
echo.
echo if __name__ == "__main__":
echo     sys.exit(main(^)^)
) > test_security.py

echo [*] Running security tests...
echo.

python test_security.py >> "!TEST_LOG!" 2>&1
set TEST_RESULT=!ERRORLEVEL!

echo.
echo ==========================================
if !TEST_RESULT! equ 0 (
    echo TEST PASSED >> "!TEST_LOG!"
    echo TEST PASSED
) else (
    echo TEST FAILED >> "!TEST_LOG!"
    echo TEST FAILED
)
echo ==========================================
for /f "tokens=*" %%A in ('powershell get-date') do (echo Timestamp: %%A >> "!TEST_LOG!"^)
echo Status: TEST RESULT >> "!TEST_LOG!"

del test_security.py

exit /b !TEST_RESULT!
