import platform
import subprocess
import datetime
import os

LOG_FILE = 'logs/test_run.log'

def log(message):
    with open(LOG_FILE, 'a') as f:
        f.write(message + '\n')

def run_test(file_name):
    system = platform.system()
    if system == 'Windows':
        cmd = ['run_test.bat', file_name]
    else:
        cmd = ['./run_test.sh', file_name]

    timestamp = datetime.datetime.now().isoformat()
    log(f"[{timestamp}] Starting test for {file_name}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        log(f"[{timestamp}] Output for {file_name}: {result.stdout}")
        if result.stderr:
            log(f"[{timestamp}] Error for {file_name}: {result.stderr}")
        status = "TEST PASSED" if result.returncode == 0 else "TEST FAILED"
    except subprocess.TimeoutExpired:
        log(f"[{timestamp}] Test for {file_name} timed out")
        status = "TEST FAILED"
    log(f"[{timestamp}] {file_name}: {status}")
    return status == "TEST PASSED"

if __name__ == "__main__":
    # Clear log
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    files = ['input_backup.py', 'input.py']
    overall_success = True
    for file in files:
        success = run_test(file)
        if not success:
            overall_success = False

    final_status = "TEST PASSED" if overall_success else "TEST FAILED"
    timestamp = datetime.datetime.now().isoformat()
    log(f"[{timestamp}] Overall: {final_status}")