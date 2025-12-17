import os
import subprocess
import platform
from datetime import datetime

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "test_run.log")

def run_and_log(cmd, env=None, file_label=None):
    """Run a command and append its output and a timestamp to the log file."""
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"--- {timestamp} | {file_label or 'test'} ---\n")
        f.write(f"Command: {cmd}\n")
    try:
        # Use shell=False for safety, but allow string parsing of cmd
        proc = subprocess.run(cmd, shell=False, capture_output=True, text=True, env=env)
        out = proc.stdout + proc.stderr
        status = "TEST PASSED" if proc.returncode == 0 else "TEST FAILED"
    except Exception as e:
        out = str(e)
        status = "TEST FAILED"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(out + "\n")
        f.write(status + "\n")
    return proc.returncode


def main():
    # detect environment
    system = platform.system().lower()

    # choose script
    if system.startswith("windows"):
        cmd = ["cmd.exe", "/c", "run_test.bat"]
    else:
        cmd = ["bash", "run_test.sh"]

    # run tests for both backup and secure file
    # backup first
    env_backup = os.environ.copy()
    env_backup["FILE_TO_TEST"] = "input_backup.py"
    ret_backup = run_and_log(cmd, env=env_backup, file_label="input_backup.py")

    # then secure
    env_secure = os.environ.copy()
    env_secure["FILE_TO_TEST"] = "input.py"
    ret_secure = run_and_log(cmd, env=env_secure, file_label="input.py")

    # final summary
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        # We show both results and consider the secure file as the success indicator
        if ret_backup == 0:
            f.write("\nBACKUP: ALL TESTS PASSED (unexpected for a vulnerable version)\n")
        else:
            f.write("\nBACKUP: TESTS FAILED (as expected for vulnerable version)\n")

        if ret_secure == 0:
            f.write("\nSECURE: ALL TESTS PASSED\n")
        else:
            f.write("\nSECURE: TESTS FAILED\n")

    # Exit with zero code only if secure file tests passed
    exit(0 if ret_secure == 0 else 1)


if __name__ == "__main__":
    main()
