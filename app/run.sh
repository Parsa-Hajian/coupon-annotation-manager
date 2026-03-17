#!/bin/bash
# ============================================================
# Coupon Annotation Manager — Launch script
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Use venv if available, otherwise system Python
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting Coupon Annotation Manager..."
echo "The app will open in your browser at http://localhost:8501"
echo ""

streamlit run app.py --server.headless true
