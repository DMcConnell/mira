#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

# Activate venv if it exists
if [ -d .venv ]; then
    source .venv/bin/activate
fi

# Allow manual override: MIRA_ENV=mac or pi
export MIRA_ENV="${MIRA_ENV:-$(uname -s | grep -q Darwin && echo mac || echo pi)}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379}"
export CONTROL_PLANE_URL="${CONTROL_PLANE_URL:-http://localhost:8090}"

echo "Starting Gesture Worker (Production Mode)"
echo "  MIRA_ENV: $MIRA_ENV"
echo "  REDIS_URL: $REDIS_URL"
echo "  CONTROL_PLANE_URL: $CONTROL_PLANE_URL"
echo ""

python src/gesture_worker_full.py

