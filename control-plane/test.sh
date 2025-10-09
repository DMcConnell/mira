#!/bin/bash

# Mira Control Plane - Test Runner

set -e

echo "🧪 Running Control Plane Tests..."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run pytest with coverage
pytest -v --cov=app --cov-report=term-missing tests/

echo "✅ All tests passed!"

