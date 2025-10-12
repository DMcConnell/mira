# Gesture Worker Architecture

## Overview

The gesture-worker is a microservice that captures video, detects hand gestures using MediaPipe, and streams data to the Mira ecosystem via **two parallel paths**:

1. **Raw Vision Stream**: Real-time gesture data for UI feedback
2. **Command Pipeline**: Debounced, high-confidence gestures as actionable commands

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          GESTURE WORKER                              │
│                                                                       │
│  ┌───────────┐    ┌──────────────┐    ┌─────────────────────────┐  │
│  │  Camera   │ -> │  MediaPipe   │ -> │  Gesture Classifier     │  │
│  │  Capture  │    │  Hand        │    │  - Static (palm/fist)   │  │
│  │           │    │  Detection   │    │  - Dynamic (swipes)     │  │
│  └───────────┘    └──────────────┘    └─────────┬───────────────┘  │
│                                                   │                   │
│                                         ┌─────────┴─────────┐        │
│                                         │                   │        │
│                                    Path 1              Path 2        │
│                                    (Raw)             (Commands)      │
└─────────────────────────────────────┼─────────────────┼─────────────┘
                                      │                 │
                                      ▼                 ▼
                            ┌──────────────────┐  ┌─────────────────┐
                            │  Redis Pub/Sub   │  │ Control Plane   │
                            │  mira:vision     │  │  /command       │
                            └────────┬─────────┘  └────────┬────────┘
                                     │                     │
                                     ▼                     ▼
                            ┌──────────────────┐  ┌─────────────────┐
                            │  Backend         │  │  Arbiter        │
                            │  /ws/vision      │  │  (Policy)       │
                            └────────┬─────────┘  └────────┬────────┘
                                     │                     │
                                     │                     ▼
                                     │            ┌─────────────────┐
                                     │            │  Redis Pub/Sub  │
                                     │            │  mira:state     │
                                     │            └────────┬────────┘
                                     │                     │
                                     │                     ▼
                                     │            ┌─────────────────┐
                                     │            │  Backend        │
                                     │            │  /ws/state      │
                                     │            └────────┬────────┘
                                     │                     │
                                     ▼                     ▼
                            ┌────────────────────────────────────────┐
                            │           FRONTEND                      │
                            │  - VisionPanel (gesture display)        │
                            │  - State updates (UI changes)          │
                            └────────────────────────────────────────┘
```

---

## Data Flow

### Path 1: Real-Time Vision Stream (UI Feedback)

**Purpose**: Provide immediate visual feedback of gesture detection to the user.

**Flow**:

1. Gesture worker detects hand and classifies gesture
2. Publishes `VisionIntent` to Redis channel `mira:vision` (10-30 times/sec)
3. Backend subscribes to `mira:vision` and forwards to `/ws/vision` WebSocket
4. Frontend `VisionPanel` displays current gesture, confidence, FPS

**Data Format** (VisionIntent):

```json
{
  "tsISO": "2025-10-12T10:30:45.123Z",
  "gesture": "palm",
  "confidence": 0.87,
  "armed": true
}
```

**Characteristics**:

- **High frequency**: Every frame (10-30 Hz)
- **Low latency**: < 100ms from detection to display
- **No filtering**: Shows all gestures including noise
- **Purpose**: User feedback, debugging, demos

---

### Path 2: Command Pipeline (State Changes)

**Purpose**: Trigger actionable state changes from high-confidence, debounced gestures.

**Flow**:

1. Gesture worker applies debouncing logic (cooldown, confidence threshold)
2. Sends `Command` to Control Plane `/command` HTTP endpoint (~ once per gesture)
3. Arbiter validates command and applies policy
4. Arbiter creates `StatePatch` and publishes to Redis `mira:state`
5. Backend subscribes to `mira:state` and forwards to `/ws/state` WebSocket
6. Frontend updates application state (e.g., navigation, mode change)

**Data Format** (Command):

```json
{
  "id": "uuid-1234",
  "ts": "2025-10-12T10:30:45.123Z",
  "source": "gesture",
  "action": "gesture_swipe_left",
  "payload": {
    "gesture": "swipe_left",
    "confidence": 0.92
  }
}
```

**Characteristics**:

- **Low frequency**: Debounced (~0.5s cooldown between commands)
- **High confidence**: Only gestures that meet threshold
- **Policy-driven**: Control Plane applies authorization/validation
- **Auditable**: Persisted in Control Plane event log
- **Purpose**: Actual UI state changes, navigation, actions

---

## Why Two Paths?

### Separation of Concerns

1. **UI Feedback vs. Actions**

   - Users need immediate visual feedback (Path 1)
   - But we don't want every gesture to trigger actions (Path 2)

2. **Performance**

   - Path 1: High throughput, simple broadcast
   - Path 2: Lower throughput, policy evaluation, persistence

3. **Reliability**

   - Path 1: Fire-and-forget, no ACKs needed
   - Path 2: HTTP with error handling, retry logic

4. **Security**
   - Path 1: Read-only, no state mutation
   - Path 2: Goes through Control Plane arbiter for validation

---

## Configuration

### Environment Variables

```bash
# gesture-worker
MIRA_ENV=mac              # "mac" or "pi" - selects camera backend
REDIS_URL=redis://localhost:6379
CONTROL_PLANE_URL=http://localhost:8090

# backend
REDIS_URL=redis://localhost:6379

# control-plane
REDIS_URL=redis://localhost:6379
```

---

## Gesture Detection Pipeline

### 1. Video Capture

- **Mac**: OpenCV with USB webcam (`cv2.VideoCapture(0)`)
- **Pi**: Picamera2 or GStreamer pipeline

### 2. MediaPipe Hand Detection

- Extracts 21 3D landmarks per hand
- Runs at ~30 FPS on Mac, ~15-20 FPS on Pi
- `model_complexity=0` for speed

### 3. Gesture Classification

**Static Gestures** (from finger extension):

- `palm`: All fingers extended
- `fist`: All fingers closed
- `point`: Index extended, others closed
- `idle`: Undefined/no hand

**Dynamic Gestures** (from centroid tracking):

- `swipe_left`: Horizontal movement < -20% screen width
- `swipe_right`: Horizontal movement > +20% screen width

### 4. Debouncing State Machine

- **IDLE**: No gesture or low confidence
- **ARMED**: Palm detected (prepares for swipe)
- **COOLDOWN**: After command sent (prevents repeats)

---

## Deployment

### Docker Compose

The gesture-worker is added as a service in `docker-compose.yml`:

```yaml
gesture-worker:
  build: ./gesture-worker
  environment:
    - MIRA_ENV=mac
    - REDIS_URL=redis://redis:6379
    - CONTROL_PLANE_URL=http://control-plane:8090
  depends_on:
    - redis
    - control-plane
```

### Running Locally (Development)

```bash
# Start Redis and Control Plane first
docker-compose up redis control-plane

# Run gesture worker locally (with GUI)
cd gesture-worker
export MIRA_ENV=mac
export REDIS_URL=redis://localhost:6379
export CONTROL_PLANE_URL=http://localhost:8090
python src/gesture_worker_full.py
```

### Running on Raspberry Pi

```bash
# Set environment for Pi camera
export MIRA_ENV=pi

# Build with Pi requirements
docker-compose build gesture-worker

# Run (may need device access or privileged mode)
docker-compose up gesture-worker
```

---

## Monitoring & Debugging

### Gesture Worker Logs

```bash
docker-compose logs -f gesture-worker
```

### Watch Vision Stream (curl)

```bash
# Test Redis vision channel
redis-cli SUBSCRIBE mira:vision
```

### Watch Commands (Control Plane logs)

```bash
docker-compose logs -f control-plane | grep gesture
```

### Frontend Debug

- Open VisionPanel to see real-time gesture display
- Check browser console for WebSocket connection status
- Monitor FPS and confidence values

---

## Performance Tuning

### Target Metrics

- **Mac**: 20-30 FPS, < 50ms latency
- **Pi 4/5**: 12-20 FPS, < 120ms latency

### Optimization Levers

1. **Resolution**: 640x360 (default) → 480x270 (faster)
2. **Model complexity**: 0 (fastest) vs. 1 (more accurate)
3. **Max hands**: 1 (fastest) vs. 2 (more features)
4. **Detection confidence**: 0.4 (sensitive) → 0.6 (strict)
5. **Tracking confidence**: 0.4 (sensitive) → 0.6 (strict)

---

## Future Enhancements

### Short-term

- [ ] Add snapshot endpoint for still image capture
- [ ] Implement gesture confidence weighting
- [ ] Add multi-hand gesture support (two-hand interactions)
- [ ] Per-user gesture sensitivity settings

### Long-term

- [ ] Custom gesture model training
- [ ] Body pose detection (MediaPipe Holistic)
- [ ] Gesture macro recording/playback
- [ ] Voice + gesture multimodal commands

---

## Troubleshooting

### Camera not detected

- **Mac**: Check camera permissions in System Preferences
- **Pi**: Verify `libcamera` is installed and camera is enabled
- **Docker**: Ensure device access with `--device` or `privileged: true`

### Redis connection failed

- Verify Redis is running: `docker-compose ps redis`
- Check REDIS_URL environment variable
- Test connection: `redis-cli ping`

### No gestures detected

- Check lighting (avoid backlight)
- Ensure hand is in frame and visible
- Lower detection confidence threshold
- Check MediaPipe model download

### High latency / Low FPS

- Reduce resolution or model complexity
- Close other applications using camera
- On Pi: disable desktop compositing for kiosk mode

---

## Related Documentation

- [Gesture Control Stack Guide](../docs/mira_gesture_control_stack_guide_mac_raspberry_pi.md)
- [Phase 2 Control Plane Architecture](../docs/mira_phase2_detailed.md)
- [MediaPipe Hands Documentation](https://google.github.io/mediapipe/solutions/hands)
