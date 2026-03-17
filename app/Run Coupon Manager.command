#!/bin/bash
# Double-click this file on macOS to launch the app
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting Coupon Annotation Manager..."
echo ""

streamlit run app.py

# Keep window open if there's an error
read -p "Press Enter to close..."
