#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate

# Allow manual override: MIRA_ENV=mac or pi
export MIRA_ENV="${MIRA_ENV:-$(uname -s | grep -q Darwin && echo mac || echo pi)}"

python gesture_worker.py
