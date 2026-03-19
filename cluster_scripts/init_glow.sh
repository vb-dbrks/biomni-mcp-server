#!/bin/bash
# Init script: installs Glow library for Spark pipe transformer
set -e

echo "=== Installing Glow ==="
pip install glow.py

echo "=== Glow installed ==="
python -c "import glow; print(f'Glow version: {glow.__version__}')"
