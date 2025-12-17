#!/usr/bin/env bash
set -euo pipefail

# Install Python dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
