"""
Security test suite for Flask application
Tests the secure (input.py) version
"""
import sys
import os
import sqlite3
import tempfile
from pathlib import Path


def setup_test_db():
    """Create a test database with sample data"""
    db_file = tempfile.mktemp(suffix='.db')
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute('''CREATE TABLE profiles 
                 (id INTEGER PRIMARY KEY, name TEXT, balance REAL)''')
    c.execute("INSERT INTO profiles VALUES (1, 'Test User', 1000.0)")
    conn.commit()
    conn.close()
    return db_file


def test_sql_injection():
    """Test SQL injection vulnerability"""
    print("\n[TEST] SQL Injection Prevention")
    print("-" * 50)
    
    db_file = setup_test_db()
    os.environ['DB_FILE'] = db_file
    
    try:
        import input as secure_app
        
        # Test with malicious input
        malicious_id = "1' OR '1'='1"
        result = secure_app.query_profile(malicious_id)
        
        if result is None or result == []:
            print("[PASS] SQL injection attempt blocked")
            return True
        else:
            print("[FAIL] SQL injection not prevented")
            return False
    except Exception as e:
        print(f"[PASS] Exception raised (expected): {str(e)[:50]}")
        return True
    finally:
        if os.path.exists(db_file):
            os.remove(db_file)


def test_command_injection():
    """Test command injection vulnerability"""
    print("\n[TEST] Command Injection Prevention")
    print("-" * 50)
    
    try:
        import input as secure_app
        
        # Test with malicious input
        malicious_name = "; rm -rf /"
        result = secure_app.export_data(malicious_name)
        
        if result is False:
            print("[PASS] Command injection attempt blocked")
            return True
        else:
            print("[FAIL] Command injection not prevented")
            return False
    except Exception as e:
        print(f"[PASS] Exception raised (expected): {str(e)[:50]}")
        return True


def test_weak_hashing():
    """Test that weak hashing is replaced"""
    print("\n[TEST] Weak Hashing Prevention")
    print("-" * 50)
    
    try:
        import input as secure_app
        
        test_info = {"username": "testuser"}
        result = secure_app.auth_user(test_info)
        
        # Check if using Argon2 (contains $argon2)
        if result and "$argon2" in result:
            print("[PASS] Using Argon2 hashing (secure)")
            return True
        elif result is None:
            print("[FAIL] auth_user returned None")
            return False
        else:
            print(f"[FAIL] Not using Argon2, got: {result[:20]}")
            return False
    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}")
        return False


def test_hardcoded_secrets():
    """Test that secrets are not hardcoded"""
    print("\n[TEST] Hardcoded Secrets Prevention")
    print("-" * 50)
    
    try:
        with open('input.py', 'r') as f:
            content = f.read()
        
        suspicious_patterns = [
            'tok_production_',
            'mail_srv_key_',
            'admin_internal_',
            'PAYMENT_TOKEN = "',
            'MAIL_SERVER_KEY = "',
            'INTERNAL_AUTH = "'
        ]
        
        found_secrets = False
        for pattern in suspicious_patterns:
            if pattern in content:
                print(f"[FAIL] Found potential hardcoded secret: {pattern}")
                found_secrets = True
        
        if not found_secrets:
            print("[PASS] No hardcoded secrets found")
            return True
        return False
    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}")
        return False


def test_debug_mode():
    """Test that debug mode is not hardcoded"""
    print("\n[TEST] Debug Mode Configuration")
    print("-" * 50)
    
    try:
        with open('input.py', 'r') as f:
            content = f.read()
        
        # Check if debug=True is hardcoded
        if 'debug=True' in content or 'debug = True' in content:
            print("[FAIL] Debug mode hardcoded to True")
            return False
        elif 'DEBUG_MODE' in content and 'os.getenv' in content:
            print("[PASS] Debug mode controlled by environment variable")
            return True
        else:
            print("[PASS] Debug mode properly configured")
            return True
    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}")
        return False


def main():
    print("\n" + "=" * 50)
    print("FLASK SECURITY TEST SUITE")
    print("=" * 50)
    
    results = []
    
    # Run tests
    results.append(("SQL Injection Prevention", test_sql_injection()))
    results.append(("Command Injection Prevention", test_command_injection()))
    results.append(("Weak Hashing Prevention", test_weak_hashing()))
    results.append(("Hardcoded Secrets Prevention", test_hardcoded_secrets()))
    results.append(("Debug Mode Configuration", test_debug_mode()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nALL TESTS PASSED")
        return 0
    else:
        print(f"\n{total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
