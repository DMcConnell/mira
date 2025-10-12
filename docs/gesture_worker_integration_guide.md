# Gesture Worker Integration Guide

## Overview

This guide explains the **recommended architecture** for integrating the gesture-worker into your Mira backend to stream gesture detection data to the frontend.

## Architecture Decision: Dual-Path Approach

The gesture-worker uses a **hybrid dual-path architecture** that balances real-time feedback with reliable command processing:

```
┌─────────────────────────────────────────────────────────────────────┐
│                       GESTURE WORKER                                 │
│  Video → MediaPipe → Gesture Classification                          │
└──────────────────┬────────────────────┬──────────────────────────────┘
                   │                    │
            PATH 1: Vision Stream   PATH 2: Commands
            (UI Feedback)           (State Changes)
                   │                    │
                   ▼                    ▼
           ┌───────────────┐    ┌──────────────┐
           │ Redis Pub/Sub │    │ HTTP POST    │
           │ mira:vision   │    │ /command     │
           └───────┬───────┘    └──────┬───────┘
                   │                    │
                   ▼                    ▼
           ┌───────────────┐    ┌──────────────┐
           │ Backend       │    │ Control      │
           │ /ws/vision    │    │ Plane        │
           │ WebSocket     │    │ Arbiter      │
           └───────┬───────┘    └──────┬───────┘
                   │                    │
                   │                    ▼
                   │            ┌──────────────┐
                   │            │ Redis Pub/Sub│
                   │            │ mira:state   │
                   │            └──────┬───────┘
                   │                    │
                   │                    ▼
                   │            ┌──────────────┐
                   │            │ Backend      │
                   │            │ /ws/state    │
                   │            └──────┬───────┘
                   │                    │
                   ▼                    ▼
           ┌──────────────────────────────────┐
           │         FRONTEND                 │
           │  - VisionPanel (live preview)    │
           │  - State (UI actions)            │
           └──────────────────────────────────┘
```

## Why Two Paths?

### Path 1: Vision Stream (Real-Time Feedback)

- **Purpose**: Give users immediate visual feedback of gesture detection
- **Flow**: Gesture Worker → Redis (`mira:vision`) → Backend → WebSocket (`/ws/vision`) → Frontend VisionPanel
- **Frequency**: High (10-30 Hz) - every frame
- **Data**: Raw gesture intents (gesture, confidence, armed state)
- **Latency**: < 100ms end-to-end
- **Use Case**: Display current gesture, FPS counter, confidence meter

### Path 2: Command Pipeline (State Changes)

- **Purpose**: Trigger actionable state changes from high-confidence gestures
- **Flow**: Gesture Worker → HTTP → Control Plane `/command` → Arbiter → Redis (`mira:state`) → Backend → WebSocket (`/ws/state`) → Frontend
- **Frequency**: Low (~1 per 0.5s) - debounced
- **Data**: Commands with validation (source, action, payload)
- **Latency**: < 200ms with policy evaluation
- **Use Case**: Navigation, mode changes, UI actions

### Benefits of Separation

1. **Performance**: High-frequency streaming (Path 1) doesn't block command processing (Path 2)
2. **Reliability**: Commands go through validation/policy (Path 2), streaming is fire-and-forget (Path 1)
3. **Security**: Commands are authenticated and audited (Path 2), streaming is read-only (Path 1)
4. **UX**: Users see immediate feedback (Path 1) even if commands are being debounced (Path 2)
5. **Debugging**: Can monitor raw detection (Path 1) separately from actions (Path 2)

## Implementation Details

### Gesture Worker (`gesture_worker_full.py`)

The worker:

1. Captures video frames from camera
2. Runs MediaPipe hand detection
3. Classifies gestures (palm, fist, swipe, etc.)
4. **Publishes** raw intents to Redis every frame (Path 1)
5. **Posts** debounced commands to Control Plane (Path 2)

Key features:

- Debouncing: 500ms cooldown between commands
- Confidence thresholds: Only high-confidence gestures trigger commands
- Armed state: Palm gesture "arms" the system for swipes

### Backend Vision WebSocket (`backend/app/ws/vision.py`)

Updated from mock data to real Redis subscriber:

```python
async def redis_vision_subscriber():
    """Subscribe to mira:vision and forward to WebSocket clients"""
    r = await aioredis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    await pubsub.subscribe("mira:vision")

    async for msg in pubsub.listen():
        if msg["type"] == "message":
            data = json.loads(msg["data"])
            # Broadcast to all /ws/vision clients
            for client in vision_clients:
                await client.send_json(data)
```

Started on backend startup:

```python
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(state_ws.redis_subscriber())
    asyncio.create_task(vision_ws.redis_vision_subscriber())  # NEW
```

### Control Plane Arbiter

Already has gesture command handling:

```python
elif cmd.action.startswith("gesture_"):
    gesture = cmd.payload.get("gesture", "idle")
    patch = StatePatch(path="/last_gesture", value=gesture)
    await publish_state(patch.dict())
    # Persisted to SQLite event log
```

### Frontend VisionPanel

Already connects to `/ws/vision` WebSocket:

```typescript
const ws = new WebSocket(getVisionWebSocketUrl());
ws.onmessage = (event) => {
  const intent: VisionIntent = JSON.parse(event.data);
  setLatestIntent(intent); // Display gesture, confidence, armed
};
```

## Alternative Approaches Considered

### ❌ Option A: Direct WebSocket from Gesture Worker to Frontend

**Why not?**

- Worker would need to manage WebSocket connections (complex)
- No command validation/policy enforcement
- Harder to scale horizontally
- Mixing transport concerns with business logic

### ❌ Option B: Gesture Worker → Backend Only (No Control Plane)

**Why not?**

- Loses command/event architecture benefits
- No audit trail of gesture commands
- Can't apply policy (e.g., require confirmation for sensitive gestures)
- Doesn't fit Phase 2 architecture

### ❌ Option C: Single Path (Commands Only)

**Why not?**

- No real-time visual feedback while cooldown is active
- Can't show "almost triggered" states
- Harder to debug detection issues
- Poor UX for users who want to see what the camera sees

## Deployment

### Docker Compose

Added to `docker-compose.yml`:

```yaml
gesture-worker:
  build: ./gesture-worker
  environment:
    - MIRA_ENV=${MIRA_ENV:-mac}
    - REDIS_URL=redis://redis:6379
    - CONTROL_PLANE_URL=http://control-plane:8090
  depends_on:
    - redis
    - control-plane
```

### Local Development (Mac)

```bash
# Start dependencies
docker-compose up redis control-plane backend

# Run gesture worker locally (with GUI window)
cd gesture-worker
export REDIS_URL=redis://localhost:6379
export CONTROL_PLANE_URL=http://localhost:8090
make run
```

### Production (Raspberry Pi)

```bash
# Set Pi environment
export MIRA_ENV=pi

# Run all services
docker-compose up --build

# Or run gesture-worker on host (for better camera access)
cd gesture-worker
make setup
MIRA_ENV=pi make run
```

## Monitoring & Debugging

### Check Vision Stream

**Redis**:

```bash
redis-cli SUBSCRIBE mira:vision
```

**Backend logs**:

```bash
docker-compose logs -f server | grep Vision
# Should show: "[Vision WS] Subscribed to Redis channel: mira:vision"
```

**Frontend**:

- Open VisionPanel component
- Should show live gesture, confidence, FPS
- Check browser console for WebSocket status

### Check Command Pipeline

**Control Plane logs**:

```bash
docker-compose logs -f control-plane | grep gesture
# Should show: "Processing command: gesture_swipe_left from gesture"
```

**State updates**:

```bash
redis-cli SUBSCRIBE mira:state
# Should show state patches when gestures trigger
```

**Event log**:

```bash
sqlite3 control-plane/data/control_plane.db "SELECT * FROM events WHERE type='gesture' LIMIT 10"
```

## Performance Considerations

### Latency Budget

| Component             | Target Latency |
| --------------------- | -------------- |
| Gesture detection     | 30-50ms        |
| Redis publish         | 1-5ms          |
| Backend forward       | 1-5ms          |
| WebSocket send        | 1-5ms          |
| **Total (Path 1)**    | **< 100ms**    |
| HTTP to Control Plane | 10-20ms        |
| Arbiter processing    | 5-10ms         |
| State broadcast       | 5-10ms         |
| **Total (Path 2)**    | **< 200ms**    |

### Throughput

- **Vision stream**: ~10-30 messages/sec (depends on camera FPS)
- **Commands**: ~1-2 commands/sec (limited by cooldown)
- **Redis**: Can handle 100k+ ops/sec (not a bottleneck)
- **WebSocket**: Can handle 1000+ concurrent clients

### Scaling

- Multiple gesture workers can publish to same Redis channel (e.g., multiple cameras)
- Backend can horizontally scale (each instance subscribes to Redis)
- Frontend clients are load-balanced by WebSocket connections
- Control Plane can be scaled with Redis-based distributed locking

## Security Considerations

### Path 1 (Vision Stream)

- **Read-only**: No state mutation possible
- **Public**: OK to expose (just gesture names/confidence)
- **No auth required**: Visual feedback for all users

### Path 2 (Command Pipeline)

- **Write access**: Can change application state
- **Authenticated**: Commands go through Control Plane
- **Audited**: All commands logged in SQLite
- **Rate limited**: Cooldown prevents spam

### Recommendations

1. Add JWT auth to `/command` endpoint in production
2. Implement per-user gesture sensitivity settings
3. Log suspicious patterns (e.g., rapid repeated gestures)
4. Consider adding confirmation for sensitive gestures

## Testing

### Unit Tests

```bash
# Test gesture classification
python -m pytest tests/test_gesture_classifier.py

# Test Redis publishing
python -m pytest tests/test_redis_publisher.py
```

### Integration Tests

```bash
# Test full pipeline
docker-compose up -d
curl http://localhost:8090/health  # Control Plane
curl http://localhost:8080/health  # Backend
redis-cli SUBSCRIBE mira:vision    # Watch stream
```

### End-to-End Tests

1. Start all services
2. Open frontend at `http://localhost`
3. Perform gestures in front of camera
4. Verify:
   - VisionPanel shows live gesture
   - Console logs show WebSocket messages
   - State updates when command triggered
   - Control Plane logs show command processing

## Troubleshooting

### No vision data in frontend

1. Check gesture-worker is running and connected to Redis
2. Check backend has started `redis_vision_subscriber()`
3. Check frontend WebSocket is connected to `/ws/vision`
4. Check Redis is accessible: `redis-cli ping`

### Commands not triggering

1. Check gesture cooldown hasn't blocked command
2. Check confidence threshold is met
3. Check Control Plane is reachable: `curl http://localhost:8090/health`
4. Check Control Plane logs for rejected commands

### High latency

1. Reduce camera resolution (640x360 → 480x270)
2. Lower MediaPipe model complexity (use 0)
3. Reduce max hands (use 1 instead of 2)
4. Check Redis latency: `redis-cli --latency`
5. Check network latency between services

## Future Enhancements

### Short-term

- [ ] Add gesture recording/replay for testing
- [ ] Implement per-user gesture sensitivity profiles
- [ ] Add snapshot endpoint for still image capture
- [ ] WebRTC for low-latency video streaming

### Long-term

- [ ] Multi-camera support (multiple workers)
- [ ] Custom gesture model training
- [ ] Gesture macros (sequences)
- [ ] Voice + gesture multimodal commands

## Conclusion

The **dual-path architecture** is the recommended approach because it:

✅ Provides immediate visual feedback (Path 1)  
✅ Ensures reliable command processing (Path 2)  
✅ Fits into existing Phase 2 Control Plane architecture  
✅ Separates concerns (streaming vs. actions)  
✅ Scales independently (high-frequency stream, low-frequency commands)  
✅ Provides security and audit trail for commands  
✅ Easy to monitor and debug each path separately

This architecture has been implemented and is ready to use. See [gesture-worker/QUICKSTART.md](../gesture-worker/QUICKSTART.md) to get started.

## Resources

- [Gesture Worker README](../gesture-worker/README.md)
- [Gesture Worker Architecture](../gesture-worker/ARCHITECTURE.md)
- [Gesture Control Stack Guide](./mira_gesture_control_stack_guide_mac_raspberry_pi.md)
- [Phase 2 Control Plane Details](./mira_phase2_detailed.md)
