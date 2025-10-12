#!/usr/bin/env bash
# Run gesture worker natively on Raspberry Pi OS
# This script sets up the environment and runs the worker

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Mira Gesture Worker (Native Pi OS) ===${NC}\n"

# Check if running on Raspberry Pi
if [[ ! -f /proc/device-tree/model ]] || ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    echo -e "${YELLOW}Warning: This doesn't appear to be a Raspberry Pi${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Change to gesture-worker directory
cd "$(dirname "$0")"

# Environment configuration
export MIRA_ENV=pi
export REDIS_URL=${REDIS_URL:-redis://localhost:6379}
export CONTROL_PLANE_URL=${CONTROL_PLANE_URL:-http://localhost:8090}

echo -e "${GREEN}Environment:${NC}"
echo "  MIRA_ENV: $MIRA_ENV"
echo "  REDIS_URL: $REDIS_URL"
echo "  CONTROL_PLANE_URL: $CONTROL_PLANE_URL"
echo

# Check if venv exists
if [[ ! -d ".venv" ]]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements/base.txt -r requirements/pi.txt
else
    source .venv/bin/activate
fi

# Check system dependencies
echo -e "${GREEN}Checking system dependencies...${NC}"

if ! python3 -c "from picamera2 import Picamera2" 2>/dev/null; then
    echo -e "${RED}Error: Picamera2 not found${NC}"
    echo "Install with: sudo apt-get install -y python3-picamera2 python3-libcamera libcamera-apps"
    exit 1
fi

echo -e "${GREEN}✓ Picamera2 available${NC}"

# Check if Redis is accessible
echo -e "${GREEN}Checking Redis connection...${NC}"
if ! redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to Redis at $REDIS_URL${NC}"
    echo "Make sure Docker services are running:"
    echo "  cd .. && docker-compose -f docker-compose.pi.yml up -d"
    exit 1
fi

echo -e "${GREEN}✓ Redis is accessible${NC}"

# Check if Control Plane is accessible
echo -e "${GREEN}Checking Control Plane connection...${NC}"
if ! curl -s -f "$CONTROL_PLANE_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to Control Plane at $CONTROL_PLANE_URL${NC}"
    echo "Make sure Docker services are running:"
    echo "  cd .. && docker-compose -f docker-compose.pi.yml up -d"
    exit 1
fi

echo -e "${GREEN}✓ Control Plane is accessible${NC}"
echo

# Check camera
echo -e "${GREEN}Checking camera...${NC}"
if ! vcgencmd get_camera 2>/dev/null | grep -q "detected=1"; then
    echo -e "${YELLOW}Warning: Camera not detected${NC}"
    echo "Enable camera: sudo raspi-config → Interface Options → Camera"
fi

echo

# Run the worker
echo -e "${GREEN}🚀 Starting Gesture Worker...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}\n"

python src/gesture_worker_full.py

