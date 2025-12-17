#!/usr/bin/env python3
"""
Automatic test execution script with environment detection
Tests both input_backup.py and input.py in sequence
Logs results with timestamps and determines overall success/failure
"""

import sys
import os
import subprocess
import platform
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "test_run.log"

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def detect_environment():
    """Detect the current environment (Windows/Linux/Docker)"""
    system = platform.system()
    logger.info(f"Detected OS: {system}")
    
    # Check if running in Docker
    if Path("/.dockerenv").exists():
        return "docker"
    elif system == "Windows":
        return "windows"
    else:
        return "linux"


def get_test_script(environment):
    """Get the appropriate test script for the environment"""
    if environment == "windows":
        return "test_security_windows.py"
    else:
        return "run_test.sh"


def run_test_file(file_name, environment, is_vulnerable=False):
    """Run tests for a specific file and return results
    
    Args:
        file_name: Name of the Python file to test
        environment: 'windows', 'linux', or 'docker'
        is_vulnerable: If True, expects vulnerabilities; if False, expects them to be fixed
    """
    logger.info(f"\n{'='*60}")
    if is_vulnerable:
        logger.info(f"Testing VULNERABLE Version: {file_name}")
        logger.info(f"(Expecting vulnerabilities to be present)")
    else:
        logger.info(f"Testing SECURE Version: {file_name}")
        logger.info(f"(Expecting vulnerabilities to be fixed)")
    logger.info(f"Environment: {environment}")
    logger.info(f"Start Time: {datetime.now().isoformat()}")
    logger.info(f"{'='*60}")
    
    # Use test_security_windows for secure version, test_vulnerable for vulnerable
    if is_vulnerable:
        test_script = "test_vulnerable_windows.py"
    else:
        test_script = "test_security_windows.py"
    
    if not Path(test_script).exists():
        logger.error(f"Test script not found: {test_script}")
        return False
    
    try:
        if environment == "windows":
            # Run Python test script on Windows using the venv Python
            venv_python = Path(".venv") / "Scripts" / "python.exe"
            if not venv_python.exists():
                # Fallback to system Python
                venv_python = "python"
            
            result = subprocess.run(
                [str(venv_python), test_script],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
        else:
            # Run shell script on Linux/macOS/Docker
            result = subprocess.run(
                ["bash", f"test_vulnerable_linux.sh" if is_vulnerable else "run_test.sh"],
                capture_output=True,
                text=True,
                timeout=300
            )
        
        # Log output
        if result.stdout:
            logger.info("STDOUT:")
            logger.info(result.stdout)
        
        if result.stderr:
            logger.warning("STDERR:")
            logger.warning(result.stderr)
        
        success = result.returncode == 0
        logger.info(f"Exit Code: {result.returncode}")
        logger.info(f"End Time: {datetime.now().isoformat()}")
        logger.info(f"Status: {'PASS' if success else 'FAIL'}")
        
        return success
        
    except subprocess.TimeoutExpired:
        logger.error(f"Test timeout for {file_name}")
        return False
    except Exception as e:
        logger.error(f"Error running test for {file_name}: {e}")
        return False


def validate_environment():
    """Validate that required files and dependencies are present"""
    logger.info("\nValidating environment...")
    
    required_files = [
        "input.py",
        "input_backup.py",
        "requirements.txt"
    ]
    
    for file in required_files:
        if not Path(file).exists():
            logger.error(f"Required file missing: {file}")
            return False
        logger.info(f"✓ Found: {file}")
    
    # Check if Python packages are installed
    try:
        import flask
        import requests
        logger.info("✓ Required Python packages are installed")
        return True
    except ImportError as e:
        logger.warning(f"Missing dependency: {e}")
        logger.info("Run: pip install -r requirements.txt")
        return False


def setup_environment_variables():
    """Setup required environment variables"""
    logger.info("\nSetting up environment variables...")
    
    env_vars = {
        "FLASK_ENV": "testing",
        "FLASK_DEBUG": "False",
        "PAYMENT_TOKEN": "test_token_12345",
        "MAIL_SERVER_KEY": "test_mail_key_67890",
        "INTERNAL_AUTH": "test_auth_abcde"
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        logger.info(f"  {key} = {value}")


def main():
    """Main test execution function"""
    logger.info("\n" + "="*60)
    logger.info("AUTOMATIC SECURITY TEST EXECUTION")
    logger.info("="*60)
    logger.info(f"Start Time: {datetime.now().isoformat()}")
    
    # Detect environment
    environment = detect_environment()
    logger.info(f"Environment Detected: {environment}")
    
    # Validate environment
    if not validate_environment():
        logger.warning("Environment validation had issues, but continuing...")
    
    # Setup environment variables
    setup_environment_variables()
    
    # Create configs directory for testing
    Path("configs").mkdir(exist_ok=True)
    
    # Create test config file
    config_file = Path("configs") / "test_config.yaml"
    if not config_file.exists():
        logger.info(f"Creating test config file: {config_file}")
        config_file.write_text("""app:
  name: TestApp
  version: 1.0
  debug: false
database:
  path: appdata.db
  timeout: 30
""")
    
    # Run tests
    results = {}
    
    logger.info("\n" + "="*60)
    logger.info("PHASE 1: Testing Vulnerable Version (input_backup.py)")
    logger.info("="*60)
    
    results["vulnerable"] = run_test_file("input_backup.py", environment, is_vulnerable=True)
    
    logger.info("\n" + "="*60)
    logger.info("PHASE 2: Testing Secure Version (input.py)")
    logger.info("="*60)
    
    results["secure"] = run_test_file("input.py", environment, is_vulnerable=False)
    
    # Print final summary
    logger.info("\n" + "="*60)
    logger.info("FINAL TEST SUMMARY")
    logger.info("="*60)
    
    logger.info(f"Vulnerable Version (input_backup.py): {'VULNERABILITIES DETECTED (expected)' if results['vulnerable'] else 'SECURE (unexpected)'}")
    logger.info(f"Secure Version (input.py): {'SECURE (expected)' if results['secure'] else 'VULNERABLE (unexpected)'}")
    
    overall_success = results['vulnerable'] and results['secure']
    
    logger.info("\n" + "="*60)
    if overall_success:
        logger.info("✓ ALL TESTS PASSED")
        final_status = "TEST PASSED"
        exit_code = 0
    else:
        logger.info("✗ SOME TESTS FAILED")
        final_status = "TEST FAILED"
        exit_code = 1
    
    logger.info(f"End Time: {datetime.now().isoformat()}")
    logger.info(f"Final Status: {final_status}")
    logger.info("="*60)
    
    # Ensure final status is in log file
    with open(log_file, 'a') as f:
        f.write(f"\n{final_status}\n")
    
    return exit_code


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
