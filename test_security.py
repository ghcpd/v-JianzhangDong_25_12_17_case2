#!/usr/bin/env python3

import subprocess
import time
import requests
import os
import sys

def wait_for_server():
    import socket
    for _ in range(50):  # 5 seconds
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('localhost', 5000))
            sock.close()
            return True
        except:
            time.sleep(0.1)
    return False

def test_vulnerabilities(file_name):
    # Set environment variables
    os.environ['PAYMENT_TOKEN'] = 'test_token'
    os.environ['MAIL_SERVER_KEY'] = 'test_key'
    os.environ['INTERNAL_AUTH'] = 'test_auth'
    os.environ['SALT'] = 'test_salt'

    # Start the Flask app
    proc = subprocess.Popen([sys.executable, file_name])
    if not wait_for_server():
        print("Server did not start")
        proc.terminate()
        proc.wait()
        return False

    vulnerabilities_found = False

    try:
        # Test SQL Injection
        response = requests.get('http://localhost:5000/profile?id=1%27%20OR%201%3D1%20--', timeout=5)
        if response.status_code == 200 and 'test' in response.text.lower():
            print("SQL Injection possible")
            vulnerabilities_found = True

        # Test Command Injection
        response = requests.get('http://localhost:5000/export?name=test%3Brm%20-rf%20%2A', timeout=5)
        if response.status_code == 200:
            print("Command Injection possible")
            vulnerabilities_found = True

        # Test Path Traversal
        response = requests.post('http://localhost:5000/config', json={'file': '../../../etc/passwd'}, timeout=5)
        if response.status_code == 200 and 'error' not in response.text.lower():
            print("Path Traversal possible")
            vulnerabilities_found = True

        # Test SSRF
        response = requests.post('http://localhost:5000/transfer', json={'target': 'test', 'amount': 100, 'notify_url': 'ftp://internal:8080'}, timeout=5)
        if response.status_code == 200 and 'Invalid' not in response.text:
            print("SSRF possible")
            vulnerabilities_found = True

    except Exception as e:
        print(f"Test error: {e}")
        vulnerabilities_found = True
    finally:
        proc.terminate()
        proc.wait()

    return not vulnerabilities_found  # True if no vulnerabilities

if __name__ == "__main__":
    file_name = sys.argv[1]
    success = test_vulnerabilities(file_name)
    sys.exit(0 if success else 1)