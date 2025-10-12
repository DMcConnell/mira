# Mira – Phase 2 Implementation Guides

> Objective: Evolve from a mocked single-process MVP into a **two-service system** — `control-plane` (Real-Time Loop + Redis + SQLite) and `app-api` (user-facing CRUD + frontend).  
> All voice and gesture inputs will now generate **Commands**, which are reduced into **StatePatches** and broadcast via Redis Pub/Sub and WebSocket.

---

## Guide 1 — Control Plane Service (FastAPI + Redis + SQLite)

### Goal

Implement the real-time command pipeline and event persistence layer.

### Output / Acceptance

- Commands, Events, and StatePatches schemas implemented.
- Arbiter Task (policies + reducers) and Broadcaster Task (Redis Pub/Sub → WS) running.
- Device Workers (fake mic + gesture) produce commands periodically.
- Events persist in SQLite (`events`, `snapshots` tables).
- Frontend receives live state via WS connection.

---

### Steps

#### 1.1 Scaffolding

```
mkdir -p smart-mirror/control-plane/{app/{api,core,models,services,workers},data,tests}
cd smart-mirror/control-plane
python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn[standard] pydantic aioredis aiosqlite asyncio pytest
```

#### 1.2 Core Schemas (`app/models/core.py`)

```python
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any
from datetime import datetime
import uuid

class Command(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    source: Literal["voice","gesture","system"]
    action: str
    payload: Dict[str, Any] = {}

class Event(BaseModel):
    id: str
    ts: str
    commandId: str
    type: Literal["accepted","rejected","state_patch"]
    payload: Dict[str, Any]

class StatePatch(BaseModel):
    ts: str
    path: str
    value: Any
```

#### 1.3 SQLite Setup (`app/services/db.py`)

```python
import aiosqlite
DB_PATH="data/control_plane.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
        CREATE TABLE IF NOT EXISTS events (
          id TEXT PRIMARY KEY,
          ts TEXT,
          commandId TEXT,
          type TEXT,
          payload TEXT
        );
        CREATE TABLE IF NOT EXISTS snapshots (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts TEXT,
          state TEXT
        );
        """)
        await db.commit()
```

#### 1.4 Redis Pub/Sub Client (`app/services/bus.py`)

```python
import aioredis, json, asyncio

REDIS_URL = "redis://redis:6379"
CHANNEL = "mira:state"

async def publish_state(patch):
    r = await aioredis.from_url(REDIS_URL)
    await r.publish(CHANNEL, json.dumps(patch))
    await r.close()

async def subscribe(callback):
    r = await aioredis.from_url(REDIS_URL)
    pubsub = r.pubsub()
    await pubsub.subscribe(CHANNEL)
    async for msg in pubsub.listen():
        if msg["type"]=="message":
            await callback(json.loads(msg["data"]))
```

#### 1.5 Arbiter and Reducer (`app/core/arbiter.py`)

```python
from .state import State
from ..models.core import Command, Event, StatePatch
from ..services.bus import publish_state
from ..services.db import init_db
import json, aiosqlite

async def handle_command(cmd: Command):
    if cmd.action.startswith("add_todo"):
        patch = StatePatch(ts=cmd.ts, path="/todos/+", value=cmd.payload)
        event = Event(id=cmd.id, ts=cmd.ts, commandId=cmd.id,
                      type="state_patch", payload=patch.dict())
        await persist_event(event)
        await publish_state(patch.dict())
        return event
    else:
        event = Event(id=cmd.id, ts=cmd.ts, commandId=cmd.id,
                      type="rejected", payload={"reason":"unknown"})
        await persist_event(event)
        return event

async def persist_event(e: Event):
    async with aiosqlite.connect("data/control_plane.db") as db:
        await db.execute("INSERT INTO events VALUES (?,?,?,?,?)",
            (e.id,e.ts,e.commandId,e.type,json.dumps(e.payload)))
        await db.commit()
```

#### 1.6 Device Workers (`app/workers/gesture.py`, `voice.py`)

```python
import asyncio, random
from ..models.core import Command
from ..core.arbiter import handle_command

GESTURES = ["idle","palm","swipe_left","swipe_right","fist"]

async def gesture_worker():
    while True:
        g = random.choice(GESTURES)
        cmd = Command(source="gesture", action=f"gesture_{g}", payload={"gesture":g})
        await handle_command(cmd)
        await asyncio.sleep(2)
```

#### 1.7 Main Assembly (`app/main.py`)

```python
import asyncio
from fastapi import FastAPI, WebSocket
from app.workers.gesture import gesture_worker
from app.services.bus import subscribe
from app.models.core import Command
from app.core.arbiter import handle_command

app = FastAPI()
clients = set()

@app.on_event("startup")
async def startup():
    asyncio.create_task(gesture_worker())

@app.websocket("/ws/state")
async def ws_state(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    async def forward(patch):
        for c in list(clients):
            await c.send_json(patch)
    await subscribe(forward)

@app.post("/command")
async def post_command(cmd: Command):
    event = await handle_command(cmd)
    return {"status": event.type, "payload": event.payload}
```

---

## Guide 2 — App API Refactor + Frontend Link

### Goal

Split existing Phase 1 backend into an **App API** service that forwards all control-related operations to the Control Plane.

### Steps

#### 2.1 Refactor Structure

```
smart-mirror/app-api/
```

Reuse `mirror-server` codebase, remove mock WS logic.

#### 2.2 New Endpoints

- `POST /api/v1/command` → proxy to Control Plane `/command`.
- `GET /api/v1/state` → returns last known snapshot (read from shared SQLite).
- `/ws/state` → subscribe directly to Redis Pub/Sub.

#### 2.3 Integrate JWT Handshake

```python
@app.post("/auth/pin")
def pin_login(pin: str = Form(...)):
    if pin == os.getenv("MIRA_PIN", "1234"):
        token = jwt.encode({"cap":["mic.toggle","cam.toggle"]}, SECRET)
        return {"token":token}
    raise HTTPException(401)
```

#### 2.4 Frontend Update

- Replace old `/ws/vision` connection with `/ws/state`.
- Render new `statePatch` messages (apply diffs to local store).
- Add simple “Connected to Control Plane” indicator.

#### 2.5 Validation

- When gesture_worker emits `gesture_swipe_right`, frontend HUD updates live.
- `POST /api/v1/command` → `add_todo` → mirrored in frontend.

---

## Guide 3 — Integration & Docker Compose Update

### Goal

Run the two-service architecture locally and on Pi with Redis + shared SQLite.

### Steps

#### 3.1 Dockerfiles

**Control Plane**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY data ./data
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8090"]
```

**App API**
Use previous backend Dockerfile, expose 8080.

#### 3.2 Redis Service & Compose

```yaml
version: '3.9'
services:
  redis:
    image: redis:7
    ports: ['6379:6379']

  control-plane:
    build: ../control-plane
    ports: ['8090:8090']
    volumes: ['../control-plane/data:/app/data']
    depends_on: [redis]

  app-api:
    build: ../app-api
    ports: ['8080:8080']
    environment:
      - CONTROL_PLANE_URL=http://control-plane:8090
    volumes: ['../control-plane/data:/app/data']
    depends_on: [control-plane]

  web:
    build: ../mirror-frontend
    ports: ['80:80']
    depends_on: [app-api]
```

#### 3.3 Local Validation

```
cd ops
docker compose up --build
curl :8080/health
curl -X POST :8080/api/v1/command -d '{"source":"voice","action":"add_todo","payload":{"text":"buy milk"}}'
```

#### 3.4 Pi Deploy

Follow Phase 1 Section 3.5 (kiosk).  
Ensure `sqlite3` file is on shared volume mounted rw.

---

### Completion Checklist

**Guide 1 - Control Plane Service** ✅ COMPLETED (Oct 9, 2025)

- [x] Commands accepted/rejected logged in `events`.
- [x] Device Workers (gesture + voice) producing commands periodically.
- [x] Arbiter Task (policies + reducers) running.
- [x] Events persist in SQLite (`events`, `snapshots` tables).
- [x] Redis Pub/Sub broadcasting state patches.
- [x] WebSocket endpoint for real-time state updates.
- [x] Core schemas (Command, Event, StatePatch) implemented.

**Guide 2 - App API Refactor** ✅ COMPLETED (Oct 9, 2025)

- [x] App API proxies commands to Control Plane.
- [x] Frontend updated to use `/ws/state` endpoint.
- [x] Auth PIN → JWT implemented.
- [x] State snapshot endpoint implemented.
- [x] Redis Pub/Sub integration in backend.
- [x] State patch handling in frontend.
- [x] Control Plane connection indicator in UI.

**Guide 3 - Integration** 🚧 PENDING

- [ ] StatePatch broadcasts visible in browser console.
- [ ] Frontend HUD mirrors live state.
- [ ] Redis + SQLite persist across restarts.
- [ ] Full docker-compose deployment tested.

---

### Fast Follows

- Add Voice worker listening to hotword service.
- Add gesture confidence and policy confirmation.
- Integrate policy rules for mic/cam toggle state.
- Optimize Redis channel naming (`mira:device:gesture`, etc.).
