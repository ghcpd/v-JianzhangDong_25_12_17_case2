#!/bin/bash
set -e

echo "=========================================="
echo "Flask Security Audit Setup (Linux/macOS)"
echo "=========================================="

# Check if Python 3.8+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "[*] Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "[*] Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "[*] Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "[*] Creating directories..."
mkdir -p configs
mkdir -p logs

# Create a sample config file for testing
echo "[*] Creating sample config file..."
cat > configs/test_config.yaml <<EOF
app:
  name: TestApp
  version: 1.0
  debug: false
database:
  path: appdata.db
  timeout: 30
EOF

# Set environment variables
echo "[*] Setting environment variables..."
export FLASK_APP=input.py
export FLASK_ENV=production
export FLASK_DEBUG=False
export PAYMENT_TOKEN="test_token_12345"
export MAIL_SERVER_KEY="test_mail_key_67890"
export INTERNAL_AUTH="test_auth_abcde"

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run the application:"
echo "  python input.py"
echo ""
echo "To run tests:"
echo "  bash run_test.sh"
echo ""
