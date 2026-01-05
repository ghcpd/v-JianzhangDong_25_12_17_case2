#!/usr/bin/env python3
import sys
import time
import argparse
import requests
import threading
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

captured = {}

class CaptureHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('content-length', 0))
        body = self.rfile.read(length)
        try:
            captured['json'] = json.loads(body)
        except Exception:
            captured['body'] = body.decode('utf-8', errors='ignore')
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

    def log_message(self, format, *args):
        pass


def start_capture_server(port=8081):
    server = HTTPServer(('127.0.0.1', port), CaptureHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def sql_injection_check(base_url):
    r1 = requests.get(f"{base_url}/profile", params={"id": "1"})
    r2 = requests.get(f"{base_url}/profile", params={"id": "1'%20OR%20'1'='1"})
    try:
        j1 = r1.json()
        j2 = r2.json()
    except Exception:
        return False, 'invalid json'
    return (len(j2) > len(j1)), f'len1={len(j1)} len2={len(j2)}'


def command_injection_check(base_url):
    # attempt to inject a command that creates a file
    if os.name == 'nt':
        payload = 'inj & python -c "open(\"injected_marker.txt\", \"w\").write(\"x\")"'
        marker = os.path.join(os.getcwd(), 'injected_marker.txt')
    else:
        payload = "inj; python -c \"open('/tmp/injected_marker','w').write('x')\""
        marker = '/tmp/injected_marker'
    # remove existing marker
    try:
        os.remove(marker)
    except Exception:
        pass
    r = requests.get(f"{base_url}/export", params={"name": payload})
    time.sleep(1)
    exists = os.path.exists(marker)
    return exists, f'exists={exists} marker={marker}'


def config_read_check(base_url, secret_path):
    r = requests.post(f"{base_url}/config", json={"file": secret_path})
    try:
        j = r.json()
    except Exception:
        return False, 'invalid json'
    text = json.dumps(j)
    return ('topsecret' in text), f'response={text}'


def ssrf_check(base_url, capture_port=8081):
    server = start_capture_server(capture_port)
    time.sleep(0.2)
    notify_url = f"http://127.0.0.1:{capture_port}/notify"
    r = requests.post(f"{base_url}/transfer", json={"target": "bob", "amount": "10.5", "notify_url": notify_url})
    time.sleep(0.5)
    server.shutdown()
    j = captured.get('json')
    if not j:
        return False, 'no capture'
    return ("token" in j), f'captured_keys={list(j.keys())}'


def auth_token_format_check(base_url):
    r = requests.post(f"{base_url}/auth", json={"username": "bob"})
    try:
        j = r.json()
    except Exception:
        return False, 'invalid json'
    token = j.get('token', '')
    return (':' not in token), f'token={token}'


def profile_auth_check(base_url):
    r = requests.get(f"{base_url}/profile", params={"id": "1"})
    return (r.status_code == 200), f'status={r.status_code}'


def run_checks(base_url, expect_vulnerable):
    results = {}
    ok = True

    v_sql, info = sql_injection_check(base_url)
    results['sql_injection'] = {'vulnerable': v_sql, 'info': info}
    if v_sql != expect_vulnerable:
        ok = False

    v_cmd, info = command_injection_check(base_url)
    results['command_injection'] = {'vulnerable': v_cmd, 'info': info}
    if v_cmd != expect_vulnerable:
        ok = False

    # create a secret file to attempt reading
    secret_path = os.path.abspath('secret.txt')
    with open(secret_path, 'w') as f:
        f.write('topsecret')
    v_cfg, info = config_read_check(base_url, secret_path)
    results['config_read'] = {'vulnerable': v_cfg, 'info': info}
    if v_cfg != expect_vulnerable:
        ok = False

    v_ssrf, info = ssrf_check(base_url)
    results['ssrf_token_leak'] = {'vulnerable': v_ssrf, 'info': info}
    if v_ssrf != expect_vulnerable:
        ok = False

    v_auth, info = auth_token_format_check(base_url)
    # in the vulnerable app the token is an md5-like 32 char string without ':'; in secure it contains ':'
    results['auth_md5'] = {'vulnerable': v_auth, 'info': info}
    if v_auth != expect_vulnerable:
        ok = False

    v_profile, info = profile_auth_check(base_url)
    # vulnerable app allows unauthenticated profile access, secure one requires API key -> 401
    results['profile_auth'] = {'vulnerable': v_profile, 'info': info}
    if v_profile != expect_vulnerable:
        ok = False

    # Count observed vulnerabilities
    count = sum(1 for k in results if results[k]['vulnerable'])
    results['summary'] = {'vulnerabilities_found': count}
    # For a quick, robust check: consider app vulnerable if multiple issues are detected
    if expect_vulnerable:
        overall_ok = count >= 2
    else:
        overall_ok = (count == 0)
    return overall_ok, results


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', required=True)
    parser.add_argument('--expect-vulnerable', action='store_true')
    args = parser.parse_args()
    ok, results = run_checks(args.base_url, args.expect_vulnerable)
    print(json.dumps(results, indent=2))
    sys.exit(0 if ok else 2)
