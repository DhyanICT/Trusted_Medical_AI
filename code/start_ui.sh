#!/bin/bash
# Start the Streamlit UI

# Get the project root (parent of code/)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT/code"

# Activate venv from project root
source "$PROJECT_ROOT/venv/bin/activate"

echo "Starting TrustMed AI UI..."
echo "Make sure the backend is running on http://127.0.0.1:8000"
echo ""
echo "⚠️  Running in headless mode (browser won't auto-open)"
echo "   Manually open: http://localhost:8501"
echo ""

# Run with headless mode to avoid browser-related crashes
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
streamlit run trustmed_ui.py \
    --server.headless true \
    --server.port 8501 \
    --browser.gatherUsageStats false

