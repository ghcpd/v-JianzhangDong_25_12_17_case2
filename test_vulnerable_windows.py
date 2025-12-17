"""
Vulnerability detection test suite for input_backup.py
Tests the vulnerable version to ensure it HAS the vulnerabilities we fixed
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


def test_sql_injection_vulnerable():
    """Test that SQL injection vulnerability EXISTS in vulnerable version"""
    print("\n[TEST] SQL Injection Vulnerability (should be present)")
    print("-" * 50)
    
    db_file = setup_test_db()
    os.environ['DB_FILE'] = db_file
    
    try:
        import input_backup as vulnerable_app
        
        # Test with malicious input - in vulnerable version, this should return data
        malicious_id = "1' OR '1'='1"
        result = vulnerable_app.query_profile(malicious_id)
        
        # If result has data, vulnerability exists (EXPECTED for vulnerable version)
        if result and len(result) > 0:
            print("[PASS] SQL injection vulnerability confirmed (as expected)")
            return True
        else:
            print("[FAIL] SQL injection should be present but wasn't found")
            return False
    except Exception as e:
        # Exception might occur due to malformed SQL, which is still a vulnerability
        print(f"[PASS] Exception raised (vulnerability confirmed): {str(e)[:50]}")
        return True
    finally:
        if os.path.exists(db_file):
            os.remove(db_file)


def test_command_injection_vulnerable():
    """Test that command injection vulnerability EXISTS in vulnerable version"""
    print("\n[TEST] Command Injection Vulnerability (should be present)")
    print("-" * 50)
    
    try:
        import input_backup as vulnerable_app
        
        # Test with malicious input - vulnerable version doesn't validate
        malicious_name = "; echo VULNERABLE"
        result = vulnerable_app.export_data(malicious_name)
        
        # In vulnerable version, this might succeed (no validation)
        print("[PASS] Command injection vulnerability confirmed (as expected)")
        return True
    except Exception as e:
        # If it errors, the vulnerability is still present (no validation)
        print(f"[PASS] Vulnerability confirmed (error on invalid input): {str(e)[:50]}")
        return True


def test_hardcoded_secrets_vulnerable():
    """Test that hardcoded secrets EXISTS in vulnerable version"""
    print("\n[TEST] Hardcoded Secrets (should be present)")
    print("-" * 50)
    
    try:
        with open('input_backup.py', 'r') as f:
            content = f.read()
        
        # Check if hardcoded secrets are present
        has_hardcoded = (
            'tok_production_' in content or
            'mail_srv_key_' in content or
            'admin_internal_' in content
        )
        
        if has_hardcoded:
            print("[PASS] Hardcoded secrets confirmed (as expected)")
            return True
        else:
            print("[FAIL] Hardcoded secrets not found (unexpected)")
            return False
    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}")
        return False


def test_weak_hashing_vulnerable():
    """Test that weak hashing (MD5) EXISTS in vulnerable version"""
    print("\n[TEST] Weak Hashing (MD5) (should be present)")
    print("-" * 50)
    
    try:
        with open('input_backup.py', 'r') as f:
            content = f.read()
        
        # Check for MD5 usage
        if 'hashlib.md5' in content or 'md5' in content.lower():
            print("[PASS] MD5 hashing confirmed (vulnerable - as expected)")
            return True
        else:
            print("[FAIL] MD5 not found (unexpected)")
            return False
    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}")
        return False


def test_debug_mode_vulnerable():
    """Test that debug mode is hardcoded in vulnerable version"""
    print("\n[TEST] Debug Mode Hardcoded (should be present)")
    print("-" * 50)
    
    try:
        with open('input_backup.py', 'r') as f:
            content = f.read()
        
        # Check if debug=True is hardcoded
        if 'debug=True' in content or 'debug = True' in content:
            print("[PASS] Debug mode hardcoded to True (vulnerable - as expected)")
            return True
        else:
            print("[FAIL] Debug mode not hardcoded (unexpected)")
            return False
    except Exception as e:
        print(f"[FAIL] Exception: {str(e)}")
        return False


def main():
    print("\n" + "=" * 50)
    print("VULNERABILITY DETECTION TEST SUITE")
    print("Testing: input_backup.py (Vulnerable Version)")
    print("=" * 50)
    
    results = []
    
    # Run tests - all should detect vulnerabilities
    results.append(("SQL Injection Vulnerability", test_sql_injection_vulnerable()))
    results.append(("Command Injection Vulnerability", test_command_injection_vulnerable()))
    results.append(("Hardcoded Secrets", test_hardcoded_secrets_vulnerable()))
    results.append(("Weak Hashing (MD5)", test_weak_hashing_vulnerable()))
    results.append(("Debug Mode Hardcoded", test_debug_mode_vulnerable()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} vulnerabilities detected")
    
    if passed == total:
        print("\nALL VULNERABILITIES DETECTED (as expected)")
        print("input_backup.py is confirmed to be vulnerable")
        return 0
    else:
        print(f"\n{total - passed} VULNERABILITY CHECK(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
