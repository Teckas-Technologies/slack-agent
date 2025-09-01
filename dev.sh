#!/bin/bash

# dev.sh - Quick development mode startup
set -e

echo "🚀 Quick Development Mode"
echo "========================"

# Set development environment
export DEBUG=True
export PORT=8000
export HOST=127.0.0.1

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Run ./start.sh for full setup"
    exit 1
fi

# Load environment
set -a
source .env
set +a

# Quick dependency check
if ! command -v uvicorn &> /dev/null; then
    echo "Installing FastAPI and uvicorn..."
    pip install fastapi 'uvicorn[standard]'
fi

# Start in development mode
echo "Starting FastAPI in development mode..."
echo "📚 Docs: http://localhost:8000/docs"
echo "🔧 Health: http://localhost:8000/health"
echo ""

uvicorn app:app --reload --port 8000 --log-level debug