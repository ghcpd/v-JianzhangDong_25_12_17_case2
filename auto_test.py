import os
import platform
import subprocess
import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "test_run.log")


def now():
    return datetime.datetime.utcnow().isoformat() + "Z"


def run_test_for(target_file):
    system = platform.system()
    is_docker = os.path.exists("/.dockerenv")
    if system == "Windows":
        cmd = ["cmd", "/c", "run_test.bat"]
    else:
        cmd = ["/bin/bash", "run_test.sh"]

    env = os.environ.copy()
    env["TARGET_FILE"] = target_file

    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True) as p:
        out, _ = p.communicate()
        rc = p.returncode

    # Log details
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{now()}] TEST RUN for {target_file}\n")
        f.write(out or "(no output)" + "\n")
        status = "TEST PASSED" if rc == 0 else "TEST FAILED"
        f.write(f"[{now()}] {status}\n\n")

    return rc == 0


def main():
    overall_ok = True
    for t in ["input_backup.py", "input.py"]:
        ok = run_test_for(t)
        overall_ok = overall_ok and ok

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{now()}] OVERALL_STATUS: {"PASSED" if overall_ok else "FAILED"}\n")

    print("All done. See logs/test_run.log for details.")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
