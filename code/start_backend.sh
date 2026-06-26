#!/bin/bash
# Start the FastAPI backend server

# Get the project root (parent of code/)
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT/code"

# Activate venv from project root
source "$PROJECT_ROOT/venv/bin/activate"

echo "Starting TrustMed AI Backend..."
echo "Make sure Neo4j is running and HUGGINGFACE_API_KEY is set!"
echo ""
echo "Note: First request may take 30-60 seconds to load models."
echo "      You can pre-load models by running: python code/preload_models.py"
echo ""
echo "Backend will be available at: http://127.0.0.1:8000"
echo "Health check: http://127.0.0.1:8000/health"
echo "Warmup (pre-load models): http://127.0.0.1:8000/warmup"
echo ""
uvicorn fastapi_server:app --reload --port 8000

