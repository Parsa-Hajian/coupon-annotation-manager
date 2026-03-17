#!/bin/bash
# ============================================================
# Coupon Annotation Manager — One-time setup
# Run this script once on a new machine to install dependencies.
# ============================================================

set -e

echo "=========================================="
echo " Coupon Annotation Manager — Setup"
echo "=========================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "Please install Python 3.10+ from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Found Python $PYTHON_VERSION"

# Navigate to app directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ""
echo "Setup complete! Run the app with:"
echo "  ./run.sh"
echo ""
echo "Or double-click 'Run Coupon Manager.command' on macOS."
