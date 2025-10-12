#!/usr/bin/env bash
set -euo pipefail

PY=python3
# Ensure 3.12 (mediapipe wheels target 3.9–3.12)
if ! $PY -c 'import sys; exit(0 if (3,9) <= sys.version_info[:2] <= (3,12) else 1)'; then
  echo "Please use Python 3.9-3.12 (3.12 recommended). Current: $($PY -V)" >&2
  exit 1
fi

# Create venv
if [ ! -d ".venv" ]; then
  $PY -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip wheel setuptools

# Base deps
pip install -r requirements/base.txt

# Detect platform
UNAME_S=$(uname -s)
UNAME_M=$(uname -m)

if [[ "$UNAME_S" == "Darwin" ]]; then
  echo "[bootstrap] Detected macOS ($UNAME_M)"
  pip install -r requirements/mac.txt
  export MIRA_ENV=mac
elif [[ "$UNAME_S" == "Linux" ]]; then
  echo "[bootstrap] Detected Linux ($UNAME_M)"
  # crude check for Pi (arm64/armv7)
  if [[ "$UNAME_M" == "aarch64" || "$UNAME_M" == "armv7l" || "$UNAME_M" == "armv6l" ]]; then
    echo "[bootstrap] Installing Raspberry Pi deps"
    echo "[bootstrap] Note: Ensure system dependencies are installed (Raspberry Pi OS):"
    echo "  sudo apt-get install -y libcamera-dev libcamera-apps python3-libcamera python3-picamera2"
    pip install -r requirements/pi.txt
    export MIRA_ENV=pi
  else
    echo "[bootstrap] Linux non-Pi: defaulting to headless OpenCV"
    pip install -r requirements/pi.txt
    export MIRA_ENV=linux
  fi
else
  echo "[bootstrap] Unknown platform: $UNAME_S"
  pip install -r requirements/mac.txt
  export MIRA_ENV=mac
fi

echo "[bootstrap] Done. Activate with: source .venv/bin/activate"
