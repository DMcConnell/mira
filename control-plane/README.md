# Mira Control Plane

The **Control Plane** is the real-time command pipeline and event persistence layer for the Mira smart mirror system.

## Architecture

### Core Components

1. **Command Pipeline**

   - Commands flow from voice, gesture, or system sources
   - Arbiter applies policy rules and reduces commands to state patches
   - Events are persisted to SQLite for audit and replay

2. **State Management**

   - In-memory state is the single source of truth
   - State patches are broadcast via Redis Pub/Sub
   - WebSocket connections deliver real-time updates to clients

3. **Device Workers**
   - Gesture worker simulates gesture detection
   - Voice worker simulates voice commands
   - In production, these interface with actual hardware/ML services

### Data Flow

```
Voice/Gesture Device → Command → Arbiter → Event + StatePatch
                                              ↓           ↓
                                          SQLite     Redis Pub/Sub
                                                          ↓
                                                    WebSocket → Frontend
```

## Setup

### Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Redis (required)
docker run -d -p 6379:6379 redis:7

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_arbiter.py -v
```

## API Endpoints

### Health Check

```bash
GET /health
```

### Get Current State

```bash
GET /state
```

Returns the current in-memory state snapshot.

### Submit Command

```bash
POST /command
Content-Type: application/json

{
  "source": "voice",
  "action": "add_todo",
  "payload": {
    "text": "Buy milk"
  }
}
```

### WebSocket State Stream

```bash
WS /ws/state
```

Connects to real-time state patch broadcast stream.

## Command Reference

### Supported Commands

| Action       | Source        | Payload                                | Description                                  |
| ------------ | ------------- | -------------------------------------- | -------------------------------------------- |
| `add_todo`   | voice/system  | `{text: string}`                       | Add a new todo item                          |
| `toggle_mic` | gesture/voice | `{}`                                   | Toggle microphone on/off                     |
| `toggle_cam` | gesture/voice | `{}`                                   | Toggle camera on/off                         |
| `set_mode`   | voice/gesture | `{mode: string}`                       | Change UI mode (idle/voice/gesture/settings) |
| `gesture_*`  | gesture       | `{gesture: string, confidence: float}` | Gesture detected                             |

## State Schema

```json
{
  "mode": "idle",
  "todos": [
    {
      "id": 1,
      "text": "Example todo",
      "completed": false,
      "created_at": "2025-10-09T12:00:00"
    }
  ],
  "mic_enabled": false,
  "cam_enabled": false,
  "last_gesture": "idle",
  "last_updated": "2025-10-09T12:00:00"
}
```

## Database Schema

### Events Table

```sql
CREATE TABLE events (
  id TEXT PRIMARY KEY,
  ts TEXT NOT NULL,
  commandId TEXT NOT NULL,
  type TEXT NOT NULL,  -- accepted, rejected, state_patch
  payload TEXT NOT NULL  -- JSON
);
```

### Snapshots Table

```sql
CREATE TABLE snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  state TEXT NOT NULL  -- JSON
);
```

## Configuration

Environment variables:

- `REDIS_URL` - Redis connection URL (default: `redis://localhost:6379`)
- `DB_PATH` - SQLite database path (default: `data/control_plane.db`)

## Production Deployment

See `docker-compose.yml` in the root directory for the full multi-service deployment configuration.

```bash
# Build and run with Docker
docker build -t mira-control-plane .
docker run -p 8090:8090 \
  -e REDIS_URL=redis://redis:6379 \
  -v $(pwd)/data:/app/data \
  mira-control-plane
```

## Development Roadmap

- [ ] Add authentication/authorization for command submission
- [ ] Implement command confirmation flow for critical actions
- [ ] Add gesture confidence thresholds
- [ ] Integrate with actual voice/gesture hardware
- [ ] Add state rehydration from snapshots on startup
- [ ] Implement command replay for debugging
- [ ] Add metrics and observability
