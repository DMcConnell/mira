# Running Gesture Worker Natively on Raspberry Pi OS

This guide covers running the gesture-worker **natively on Raspberry Pi OS** while other Mira services (Redis, Control Plane, Backend) run in Docker.

## Why Native Instead of Docker?

- **Better camera access**: Direct access to Picamera2 and libcamera
- **Better performance**: No containerization overhead for video processing
- **Easier debugging**: Direct access to system resources and logs

## Architecture

```
Raspberry Pi
├── Native: gesture-worker (Python process)
│   └── Camera access via Picamera2
│
└── Docker: Redis + Control Plane + Backend + Frontend
    └── Exposed ports accessible from host
```

## Setup Steps

### 1. Install System Dependencies on Pi OS

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install libcamera and Picamera2 dependencies
sudo apt-get install -y \
    libcamera-dev \
    libcamera-apps \
    python3-libcamera \
    python3-picamera2

# Install Python and development tools
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential

# Enable camera
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable
```

### 2. Install Gesture Worker Python Dependencies

```bash
cd ~/mira/gesture-worker

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements/base.txt -r requirements/pi.txt
```

### 3. Start Docker Services (Without Gesture Worker)

Edit your docker-compose.yml to comment out the gesture-worker service, or create a separate compose file:

**Option A: Use docker-compose with exclusion**

```bash
# From project root
cd ~/mira

# Start all services except gesture-worker
docker-compose up -d redis control-plane server web

# Verify services are running
docker-compose ps
```

**Option B: Create a separate compose file for Pi**

Create `docker-compose.pi.yml`:

```yaml
services:
  redis:
    image: redis:7
    restart: unless-stopped
    ports: ['6379:6379'] # Exposed to host
    volumes:
      - redis_data:/data

  control-plane:
    restart: unless-stopped
    build: ./control-plane
    ports: ['8090:8090'] # Exposed to host
    environment:
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - DEBUG=${DEBUG:-false}
    volumes:
      - ./control-plane/data:/app/data
    depends_on:
      - redis

  server:
    restart: unless-stopped
    build: ./backend
    ports: ['8080:8080']
    environment:
      - DATA_DIR=/app/data
      - PROVIDERS_WEATHER_MODE=${PROVIDERS_WEATHER_MODE:-mock}
      - PROVIDERS_NEWS_MODE=${PROVIDERS_NEWS_MODE:-mock}
      - CONTROL_PLANE_URL=http://control-plane:8090
      - REDIS_URL=redis://redis:6379
      - CONTROL_PLANE_DB=/app/data/control_plane.db
      - JWT_SECRET=${JWT_SECRET:-dev-secret-change-in-production}
      - MIRA_PIN=${MIRA_PIN:-1234}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - DEBUG=${DEBUG:-false}
    volumes:
      - ./control-plane/data:/app/data
    depends_on:
      - control-plane
      - redis

  web:
    restart: unless-stopped
    build: ./frontend
    ports: ['80:80']
    depends_on:
      - server
      - control-plane

volumes:
  redis_data:
```

Then run:

```bash
docker-compose -f docker-compose.pi.yml up -d --build
```

### 4. Configure Environment for Native Gesture Worker

Create a `.env` file or export variables for the native gesture worker:

```bash
# In gesture-worker directory
cd ~/mira/gesture-worker

# Create .env file
cat > .env << 'EOF'
# Environment
MIRA_ENV=pi

# Docker services are on localhost from the host's perspective
REDIS_URL=redis://localhost:6379
CONTROL_PLANE_URL=http://localhost:8090

# Optional: Enable debug logging
# LOG_LEVEL=DEBUG
EOF
```

Or export directly in your shell:

```bash
export MIRA_ENV=pi
export REDIS_URL=redis://localhost:6379
export CONTROL_PLANE_URL=http://localhost:8090
```

### 5. Run Gesture Worker

```bash
cd ~/mira/gesture-worker
source .venv/bin/activate  # If using venv

# Load environment variables if using .env file
set -a; source .env; set +a

# Run the worker
python src/gesture_worker_full.py
```

You should see:

```
[GestureWorker] Starting on pi...
[GestureWorker] Camera: 640x360 @ 30fps
[GestureWorker] ✅ Connected to Redis and Control Plane
[GestureWorker] 🚀 Started. Publishing to mira:vision | Sending commands to Control Plane
```

### 6. Create a systemd Service (Optional - Auto-start on Boot)

Create `/etc/systemd/system/mira-gesture-worker.service`:

```bash
sudo nano /etc/systemd/system/mira-gesture-worker.service
```

Add:

```ini
[Unit]
Description=Mira Gesture Worker
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/mira/gesture-worker
Environment="MIRA_ENV=pi"
Environment="REDIS_URL=redis://localhost:6379"
Environment="CONTROL_PLANE_URL=http://localhost:8090"
ExecStart=/home/pi/mira/gesture-worker/.venv/bin/python src/gesture_worker_full.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mira-gesture-worker
sudo systemctl start mira-gesture-worker

# Check status
sudo systemctl status mira-gesture-worker

# View logs
sudo journalctl -u mira-gesture-worker -f
```

## Verification

### 1. Check Gesture Worker Logs

```bash
# If running manually
# Watch console output for gestures detected

# If using systemd
sudo journalctl -u mira-gesture-worker -f
```

### 2. Check Redis Connection

```bash
# Test Redis is accessible from host
redis-cli -h localhost ping
# Should return: PONG

# Subscribe to vision channel
redis-cli -h localhost
> SUBSCRIBE mira:vision
# Move your hand in front of camera - should see messages
```

### 3. Check Control Plane

```bash
# Test Control Plane is accessible
curl http://localhost:8090/health
# Should return: {"status":"healthy",...}

# Check logs
docker-compose logs -f control-plane
```

### 4. Test Full Integration

1. Open frontend: `http://<pi-ip-address>` (or `http://localhost` if browsing on Pi)
2. Navigate to Vision Panel
3. Wave your hand - should see real-time gesture detection
4. Make a palm gesture - should see it in Vision Panel
5. Check control-plane logs for command processing

## Troubleshooting

### Camera Not Working

```bash
# Test camera
libcamera-hello

# Check if camera is detected
vcgencmd get_camera
# Should show: supported=1 detected=1

# Enable legacy camera support
sudo raspi-config
# Interface Options → Legacy Camera → Enable
```

### Redis Connection Refused

```bash
# Check Redis is running
docker-compose ps redis

# Check Redis is listening on 0.0.0.0 (not just 127.0.0.1)
docker-compose exec redis redis-cli CONFIG GET bind

# If needed, restart Redis
docker-compose restart redis
```

### Control Plane Unreachable

```bash
# Check Control Plane is running
docker-compose ps control-plane

# Check logs
docker-compose logs control-plane

# Test from host
curl http://localhost:8090/health
```

### Picamera2 Import Error

```bash
# Reinstall system packages
sudo apt-get install --reinstall python3-picamera2 python3-libcamera

# Check Python can import it
python3 -c "from picamera2 import Picamera2; print('OK')"
```

### Performance Issues

If gesture detection is slow:

1. **Lower resolution**:

   ```python
   # In gesture_worker_full.py
   worker = GestureWorker(
       width=480,   # Lower from 640
       height=270,  # Lower from 360
   )
   ```

2. **Simplify MediaPipe**:

   ```python
   self.hands = mp_hands.Hands(
       model_complexity=0,      # Keep at 0
       max_num_hands=1,         # Lower from 2
       min_detection_confidence=0.5,
       min_tracking_confidence=0.5,
   )
   ```

3. **Overclock Pi** (if needed):
   ```bash
   sudo nano /boot/config.txt
   # Add:
   # arm_freq=1800
   # over_voltage=2
   # Reboot and test stability
   ```

## Network Configuration

### Key Differences from Docker

When running in Docker, services use internal hostnames like `redis` and `control-plane`.  
When running natively on the host, use `localhost` since Docker exposes ports to the host.

| Service       | Docker Internal             | From Host (Native)       |
| ------------- | --------------------------- | ------------------------ |
| Redis         | `redis://redis:6379`        | `redis://localhost:6379` |
| Control Plane | `http://control-plane:8090` | `http://localhost:8090`  |
| Backend       | `http://server:8080`        | `http://localhost:8080`  |

### If Running on Separate Machines

If your Pi is separate from other services:

```bash
# Replace localhost with actual IPs
export REDIS_URL=redis://192.168.1.100:6379
export CONTROL_PLANE_URL=http://192.168.1.100:8090
```

## Benefits of This Setup

✅ **Better camera performance** - Direct hardware access  
✅ **Easier debugging** - Native Python environment  
✅ **Flexible development** - Edit code without rebuilding containers  
✅ **Resource efficiency** - Less overhead on Pi  
✅ **Containerized core** - Redis, Control Plane, Backend still isolated

## Going Back to Full Docker

If you want to go back to full Docker:

```bash
# Stop native gesture worker
sudo systemctl stop mira-gesture-worker
# or Ctrl+C if running manually

# Uncomment gesture-worker in docker-compose.yml
# Run full stack
docker-compose up -d --build
```
