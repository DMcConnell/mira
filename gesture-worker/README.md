# Gesture Worker

Real-time hand gesture detection service for Mira Smart Mirror using MediaPipe Hands.

## Quick Start

### Local Development (Mac)

1. **Install dependencies**:

   ```bash
   cd gesture-worker
   pip install -r requirements/base.txt -r requirements/mac.txt
   ```

2. **Set environment variables**:

   ```bash
   export MIRA_ENV=mac
   export REDIS_URL=redis://localhost:6379
   export CONTROL_PLANE_URL=http://localhost:8090
   ```

3. **Start dependencies** (in separate terminal):

   ```bash
   docker-compose up redis control-plane
   ```

4. **Run gesture worker**:

   ```bash
   python src/gesture_worker_full.py
   ```

5. **View output**:
   - A window will open showing camera feed with hand landmarks
   - Watch console for detected gestures and commands sent
   - Open frontend at `http://localhost` to see VisionPanel

### Using Docker

```bash
# Build and run all services
docker-compose up --build

# Or just gesture-worker
docker-compose up gesture-worker
```

### Raspberry Pi

When running directly on Raspberry Pi OS:

```bash
# Install system dependencies for libcamera (Raspberry Pi OS only)
sudo apt-get update
sudo apt-get install -y \
    libcamera-dev \
    libcamera-apps \
    python3-libcamera \
    python3-picamera2

# Set environment for Pi
export MIRA_ENV=pi

# Install Pi-specific dependencies
pip install -r requirements/base.txt -r requirements/pi.txt

# Run
python src/gesture_worker_full.py
```

**Note**: When running in Docker on Pi, the GStreamer fallback is used automatically (no manual setup needed).

## Supported Gestures

### Static Gestures

- **palm**: All fingers extended (arms the system for swipe detection)
- **fist**: All fingers closed
- **point**: Only index finger extended
- **idle**: No hand detected or undefined pose

### Dynamic Gestures

- **swipe_left**: Quick horizontal movement to the left (>20% screen width)
- **swipe_right**: Quick horizontal movement to the right (>20% screen width)

## Architecture

The gesture worker operates on **two parallel paths**:

### Path 1: Real-Time Vision Stream

- Publishes every frame to Redis channel `mira:vision`
- Backend forwards to WebSocket `/ws/vision`
- Frontend displays in VisionPanel (FPS, gesture, confidence)
- **High frequency** (10-30 Hz), immediate feedback

### Path 2: Command Pipeline

- Debounced, high-confidence gestures only
- Sends HTTP commands to Control Plane `/command`
- Arbiter validates and creates state patches
- Frontend receives state updates via `/ws/state`
- **Low frequency** (~1 command per 0.5s), actionable events

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed architecture documentation.

## Configuration

### Environment Variables

| Variable            | Default                  | Description                                         |
| ------------------- | ------------------------ | --------------------------------------------------- |
| `MIRA_ENV`          | `mac`                    | Environment: `mac` or `pi` (selects camera backend) |
| `REDIS_URL`         | `redis://localhost:6379` | Redis connection URL                                |
| `CONTROL_PLANE_URL` | `http://localhost:8090`  | Control Plane API URL                               |

### Camera Settings

Edit in `gesture_worker_full.py`:

```python
worker = GestureWorker(
    width=640,      # Frame width (pixels)
    height=360,     # Frame height (pixels)
    fps=30,         # Target FPS
)
```

### Gesture Detection Tuning

In `GestureWorker` class:

```python
# Debounce settings
self.cooldown_duration = 0.5  # Seconds between commands

# Swipe detection thresholds
MIN_DISPLACEMENT = 0.20  # 20% of screen width
MIN_DURATION = 0.15      # At least 150ms
MAX_DURATION = 0.50      # No more than 500ms
```

## Development

### Camera Selection (Mac)

List available cameras:

```python
from src.video_capture import list_available_cameras
list_available_cameras()
```

### Testing Without Camera

Create a mock video source:

```bash
# Record a test video
ffmpeg -f avfoundation -i "0" -t 10 test_video.mp4

# Use in code
cap = cv2.VideoCapture("test_video.mp4")
```

### Debug Output

The gesture worker prints:

- FPS in top-left of video window
- Current gesture and confidence
- Console logs when commands are sent

## Performance

### Target Metrics

- **Mac**: 20-30 FPS, < 50ms end-to-end latency
- **Raspberry Pi 4/5**: 12-20 FPS, < 120ms latency

### Optimization Tips

1. **Reduce resolution**: 640x360 → 480x270
2. **Lower model complexity**: Set `model_complexity=0` in MediaPipe
3. **Single hand mode**: Set `max_num_hands=1`
4. **Headless mode**: Use `opencv-python-headless` (no GUI)
5. **Pi-specific**: Disable desktop compositing, overclock if needed

## Troubleshooting

### Camera Not Found

**Mac**:

- Check System Preferences → Security & Privacy → Camera
- Try different camera index: `cv2.VideoCapture(1)`

**Pi**:

- Enable camera: `sudo raspi-config` → Interface Options → Camera
- Test: `libcamera-hello`
- Install: `sudo apt install python3-picamera2`

### Low FPS

- Reduce resolution or model complexity
- Close other camera applications
- Check CPU usage with `top` or `htop`
- On Pi: Use `model_complexity=0`

### Redis Connection Error

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
redis-cli -u redis://localhost:6379 ping

# Check environment variable
echo $REDIS_URL
```

### No Gestures Detected

- Ensure adequate lighting (avoid backlight)
- Hold hand clearly in frame
- Lower confidence thresholds in MediaPipe config
- Check console for MediaPipe warnings

### Commands Not Reaching Control Plane

```bash
# Check Control Plane is running
curl http://localhost:8090/health

# Watch Control Plane logs
docker-compose logs -f control-plane

# Verify CONTROL_PLANE_URL
echo $CONTROL_PLANE_URL
```

## File Structure

```
gesture-worker/
├── src/
│   ├── gesture_worker_full.py  # Production worker (dual-path)
│   ├── gesture_worker.py       # Camera abstraction helpers
│   └── video_capture.py        # Development/testing script
├── requirements/
│   ├── base.txt                # Common dependencies
│   ├── mac.txt                 # Mac-specific (empty)
│   └── pi.txt                  # Pi-specific (picamera2)
├── scripts/
│   ├── bootstrap.sh            # Setup script
│   └── run.sh                  # Run script
├── Dockerfile                  # Container image
├── Makefile                    # Build targets
├── ARCHITECTURE.md             # Detailed architecture docs
└── README.md                   # This file
```

## Integration with Mira

### Backend Integration

Backend subscribes to Redis `mira:vision` channel and forwards to WebSocket clients:

```python
# backend/app/ws/vision.py
async def redis_vision_subscriber():
    r = await aioredis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    await pubsub.subscribe("mira:vision")
    # Forward to WebSocket clients
```

### Control Plane Integration

Control Plane receives commands and applies policy:

```python
# control-plane/app/core/arbiter.py
elif cmd.action.startswith("gesture_"):
    gesture = cmd.payload.get("gesture", "idle")
    patch = StatePatch(path="/last_gesture", value=gesture)
    await publish_state(patch.dict())
```

### Frontend Integration

Frontend displays gestures in VisionPanel:

```typescript
// frontend/src/features/vision/VisionPanel.tsx
const ws = new WebSocket(getVisionWebSocketUrl());
ws.onmessage = (event) => {
  const intent: VisionIntent = JSON.parse(event.data);
  // Display gesture, confidence, armed state
};
```

## Next Steps

- [ ] Add video snapshot endpoint for still image capture
- [ ] Implement gesture recording/macro system
- [ ] Support custom gesture training
- [ ] Add multi-hand gesture combinations
- [ ] Integrate with voice commands for multimodal input

## Resources

- [MediaPipe Hands Documentation](https://google.github.io/mediapipe/solutions/hands)
- [OpenCV VideoCapture Reference](https://docs.opencv.org/4.x/d8/dfe/classcv_1_1VideoCapture.html)
- [Picamera2 Manual (Pi)](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)
- [Mira Gesture Control Guide](../docs/mira_gesture_control_stack_guide_mac_raspberry_pi.md)
