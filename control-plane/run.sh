#!/bin/bash

# Mira Control Plane - Development Runner

set -e

echo "🚀 Starting Mira Control Plane..."

# Check if Redis is running
if ! nc -z localhost 6379 2>/dev/null; then
    echo "❌ Redis is not running on localhost:6379"
    echo "   Start Redis with: docker run -d -p 6379:6379 redis:7"
    exit 1
fi

echo "✅ Redis is running"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload

