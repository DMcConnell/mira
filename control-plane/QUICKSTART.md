# Control Plane Quick Start Guide

This guide will help you get the Mira Control Plane up and running locally.

## Prerequisites

- Python 3.11 or higher
- Redis 7 or higher
- SQLite3 (usually included with Python)

## Setup Steps

### 1. Install Dependencies

```bash
cd control-plane

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt
```

### 2. Start Redis

The Control Plane requires Redis for pub/sub messaging. You can run Redis in Docker:

```bash
docker run -d -p 6379:6379 --name mira-redis redis:7
```

Or if you have Redis installed locally:

```bash
redis-server
```

Verify Redis is running:

```bash
redis-cli ping
# Should return: PONG
```

### 3. Start the Control Plane

```bash
./run.sh
```

Or manually:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload
```

You should see output like:

```
🚀 Control Plane starting up...
✅ Database initialized
✅ Background workers started
Gesture worker started
Voice worker started
Subscribed to Redis channel: mira:state
```

### 4. Verify Installation

In a new terminal, run the validation script:

```bash
cd control-plane
./validate.sh
```

This will test all endpoints and verify the acceptance criteria.

## Testing the API

### Health Check

```bash
curl http://localhost:8090/health
```

### Get Current State

```bash
curl http://localhost:8090/state | jq
```

### Submit a Command

```bash
curl -X POST http://localhost:8090/command \
  -H "Content-Type: application/json" \
  -d '{
    "source": "voice",
    "action": "add_todo",
    "payload": {"text": "Buy milk"}
  }' | jq
```

### Monitor Redis Pub/Sub

In another terminal:

```bash
redis-cli SUBSCRIBE mira:state
```

You should see state patches being broadcast as commands are processed.

## Testing WebSocket Connection

Open `test_websocket.html` in your browser, or use `websocat`:

```bash
# Install websocat: brew install websocat (macOS) or cargo install websocat
websocat ws://localhost:8090/ws/state
```

You'll receive the initial state, followed by real-time updates as workers emit commands.

## Observing Worker Activity

The gesture and voice workers will automatically start generating commands:

- **Gesture Worker**: Emits gestures every 3-5 seconds
- **Voice Worker**: Emits voice commands every 8-15 seconds

Watch the logs to see commands being processed:

```bash
# The uvicorn output will show:
Gesture worker: emitted palm
Processing command: gesture_palm from gesture
Voice worker: emitted add_todo
Processing command: add_todo from voice
```

## Database Inspection

The SQLite database is created at `data/control_plane.db`. You can inspect it:

```bash
sqlite3 data/control_plane.db

# List all tables
.tables

# View recent events
SELECT * FROM events ORDER BY ts DESC LIMIT 10;

# View snapshots
SELECT * FROM snapshots ORDER BY ts DESC LIMIT 5;

# Exit
.exit
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test
pytest tests/test_arbiter.py -v
```

## Docker Deployment

### Build the Image

```bash
docker build -t mira-control-plane .
```

### Run with Docker Compose

From the project root:

```bash
docker compose up --build
```

This will start:

- Redis
- Control Plane
- Backend (app-api)
- Frontend

## Troubleshooting

### Redis Connection Error

If you see `Error subscribing to Redis`:

1. Check Redis is running: `redis-cli ping`
2. Verify the URL: `echo $REDIS_URL` (should be `redis://localhost:6379` or `redis://redis:6379` in Docker)

### Database Lock Error

If you get "database is locked":

1. Ensure no other processes are accessing the database
2. Stop all uvicorn instances
3. Remove the lock file: `rm data/control_plane.db-journal`

### Port Already in Use

If port 8090 is already in use:

1. Find the process: `lsof -i :8090`
2. Kill it: `kill -9 <PID>`
3. Or change the port in `run.sh`

## Next Steps

1. **Integrate with Frontend**: Update frontend to connect to `ws://localhost:8090/ws/state`
2. **Customize Workers**: Modify gesture/voice workers to suit your needs
3. **Add New Commands**: Extend `app/core/arbiter.py` with new command handlers
4. **Deploy to Pi**: Follow the deployment guide in the main README

## Useful Commands

```bash
# View real-time logs
tail -f data/control_plane.log  # if logging to file

# Monitor Redis activity
redis-cli MONITOR

# Check database size
du -h data/control_plane.db

# Clear database (for testing)
rm data/control_plane.db
# Restart the server to recreate
```

## Support

For issues or questions, refer to:

- Main README.md
- Phase 2 Implementation Guide (mira_phase2_detailed.md)
- Test files in `tests/` directory
