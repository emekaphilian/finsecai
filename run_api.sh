#!/bin/bash
# FinSecAI v2 API Server Startup Script
# This script runs the FastAPI backend server

set -e

echo "🚀 Starting FinSecAI v2 FastAPI Backend"
echo "========================================="

# Set environment variables if not already set
export ENVIRONMENT=${ENVIRONMENT:-"development"}
export SERVER_HOST=${SERVER_HOST:-"0.0.0.0"}
export SERVER_PORT=${SERVER_PORT:-"8000"}
export LOG_LEVEL=${LOG_LEVEL:-"INFO"}

echo "📋 Configuration:"
echo "   Environment: $ENVIRONMENT"
echo "   Host: $SERVER_HOST"
echo "   Port: $SERVER_PORT"
echo "   Log Level: $LOG_LEVEL"
echo ""

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "⚠️  FastAPI not installed. Installing dependencies..."
    pip install -r requirements.txt
fi

echo "✅ Dependencies ready"
echo ""
echo "🌐 Starting API server..."
echo "   API Docs: http://localhost:$SERVER_PORT/docs"
echo "   Redoc: http://localhost:$SERVER_PORT/redoc"
echo ""

# Start the server
python -m uvicorn api.main:app \
    --host $SERVER_HOST \
    --port $SERVER_PORT \
    --reload \
    --log-level $LOG_LEVEL
