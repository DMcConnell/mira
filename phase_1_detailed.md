# Mira – Phase 1 Implementation Guides

> Three self-contained, agent-ready guides. Vision and AI are **mocked** in these guides and treated as fast follows.

---

## Guide 1 — Backend (FastAPI) — Creation, Setup, and Code

### Goal

Create a FastAPI server that serves:

- `GET /health`
- `GET /api/v1/morning-report`
- `GET|POST|PUT|DELETE /api/v1/todos` (JSON file persistence)
- `POST /api/v1/voice/interpret` (mock intent parser)
- `GET /api/v1/settings` and `PUT /api/v1/settings` (in-memory)
- **Mock endpoints** for vision/ai: `GET /vision/snapshot.jpg` (static image), `WS /ws/vision` that sends periodic fake intents

### Output/Acceptance

- All endpoints respond with correct schemas.
- On restart, todos persist via `data/todos.json`.
- OpenAPI docs available at `/docs`.
- `pytest` for basic unit tests passes.

### Steps

#### 1.1 Project Scaffolding

```
mkdir -p smart-mirror/mirror-server/{app/{api,providers,models,ws,util},data,tests}
cd smart-mirror/mirror-server
python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn[standard] pydantic httpx python-multipart pytest
```

#### 1.2 Pydantic Models (`app/models/dto.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class CalendarItem(BaseModel):
    id: str
    title: str
    startsAtISO: str
    endsAtISO: str
    location: Optional[str] = None

class WeatherSnapshot(BaseModel):
    updatedISO: str
    tempC: float
    condition: str
    icon: str
    stale: bool = False

class NewsItem(BaseModel):
    id: str
    title: str
    source: str
    url: str
    publishedISO: str

class Todo(BaseModel):
    id: str
    text: str
    done: bool = False
    createdAtISO: str

class MorningReport(BaseModel):
    calendar: List[CalendarItem]
    weather: WeatherSnapshot
    news: List[NewsItem]
    todos: List[Todo]

class VisionIntent(BaseModel):
    tsISO: str
    gesture: str
    confidence: float
    armed: bool

class Settings(BaseModel):
    weatherMode: str = "mock"
    newsMode: str = "mock"
```

#### 1.3 Providers (mock/live stubs)

`app/providers/weather.py`, `news.py`, `calendar.py` returning deterministic mock data; include `stale` logic.

#### 1.4 Todos Service (file persistence)

`app/util/storage.py`:

```python
import json, os, tempfile
from typing import Any

DATA_DIR = os.environ.get("DATA_DIR", "data")
TODO_FILE = os.path.join(DATA_DIR, "todos.json")

def _ensure():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(TODO_FILE):
        with open(TODO_FILE, "w") as f:
            json.dump([], f)

_ensure()

def read_json(path=TODO_FILE):
    with open(path) as f: return json.load(f)

def write_json(obj: Any, path=TODO_FILE):
    fd, tmp = tempfile.mkstemp(dir=DATA_DIR)
    with os.fdopen(fd, 'w') as f: json.dump(obj, f)
    os.replace(tmp, path)
```

`app/api/todos.py` CRUD operates on that file (generate UUIDs, ISO timestamps).

#### 1.5 Morning Report & Health

`app/api/morning_report.py` aggregates provider outputs + current todos. `app/api/health.py` returns `{status:"ok"}` and a simple summary.

#### 1.6 Voice Mock

`app/api/voice.py` implements regex parsing for `switch to (ambient|morning)` and `add todo (.*)`; else `unknown`.

#### 1.7 Settings

`app/api/settings.py` stores `Settings` in-memory (module-level variable) for simplicity.

#### 1.8 Vision/AI Mocks

- `GET /vision/snapshot.jpg` returns a bundled JPEG from `app/static/snapshot.jpg`.
- `WS /ws/vision` sends a fake `VisionIntent` every 2s cycling gestures `["idle","palm","swipe_left","swipe_right","fist"]`.

#### 1.9 App Assembly (`app/main.py`)

Create FastAPI app, include routers, mount static, and add CORS.

#### 1.10 Run & Validate

```
UVICORN_CMD="uvicorn app.main:app --reload --port 8080"
$UVICORN_CMD
# Validate endpoints
curl :8080/health
curl :8080/api/v1/morning-report
curl -X POST :8080/api/v1/voice/interpret -H 'Content-Type: application/json' -d '{"text":"add todo buy milk"}'
```

#### 1.11 Tests

- `tests/test_todos.py` for CRUD
- `tests/test_morning_report.py` for schema
  Run: `pytest -q`

**Completion Checklist**

- [ ] All endpoints return 200 and schemas match.
- [ ] Todos persist across restarts.
- [ ] `/docs` renders; WS mock events are visible in browser console.
- [ ] `pytest` passes.

---

## Guide 2 — Frontend (React/Vite/TS) — Creation, Setup, and Code

### Goal

Create a SPA that renders the Morning Report, supports mode switching, shows a Settings panel, performs text-based intents, and displays a mock vision HUD + preview.

### Output/Acceptance

- Build succeeds with no TS errors.
- Dashboard shows Calendar/Weather/News/Todos with skeletons.
- Text intent modal triggers backend actions.
- Vision HUD updates via WS; snapshot preview visible.

### Steps

#### 2.1 Scaffolding

```
cd smart-mirror
npm create vite@latest mirror-frontend -- --template react-ts
cd mirror-frontend
npm i axios tailwindcss postcss autoprefixer framer-motion
npx tailwindcss init -p
```

Configure Tailwind in `tailwind.config.js` and add `@tailwind base; @tailwind components; @tailwind utilities;` to `src/styles/tailwind.css`. Import it in `src/main.tsx`.

#### 2.2 Structure

```
src/
  app/
  components/ Card.tsx, Quadrant.tsx, ModeSwitcher.tsx, Toast.tsx
  features/
    calendar/
    weather/
    news/
    todos/
    vision/
  lib/api.ts
  styles/tailwind.css
```

#### 2.3 API Client (`lib/api.ts`)

Create small wrappers using `axios` with `BASE_URL` env. Expose functions for endpoints.

#### 2.4 UI Panels

- Each panel fetches its slice of `/api/v1/morning-report` and renders with skeletons.
- To‑Dos panel includes add/complete actions calling REST endpoints optimistically.

#### 2.5 Mode Switcher

State in a top-level store (React context or simple `useState`) toggles Morning/Ambient; optional backend sync via settings.

#### 2.6 Text Command Modal

A button opens a modal input; `Enter` posts to `/api/v1/voice/interpret` and shows a success toast.

#### 2.7 Settings Panel (hidden)

Hotkey (e.g., `Ctrl+.`) toggles a drawer that shows:

- Provider modes
- App version (inject from `import.meta.env.VITE_APP_VERSION`)
- Last API latency
- Vision status: latest WS message, confidence

#### 2.8 Vision Preview & HUD (mocked)

- `<img src="/vision/snapshot.jpg" className="..." />` for preview
- WebSocket to `ws://<BASE_URL>/ws/vision`; display `gesture`, `confidence`, `armed`, and an FPS counter based on message deltas.

#### 2.9 Styling & Motion

- Keep animations light (opacity/translate) with Framer Motion.

#### 2.10 Run & Validate

```
npm run dev
# In another shell, backend running at :8080
# Visit http://localhost:5173 (or via nginx later)
```

**Completion Checklist**

- [ ] Morning Report renders from backend.
- [ ] To‑Do add/complete works; refresh retains state (server persistence).
- [ ] Modal command `add todo buy milk` adds an item.
- [ ] WS HUD updates every ~2s with mock gestures; snapshot loads.
- [ ] Hidden Settings panel opens via hotkey and shows diagnostics.

---

## Guide 3 — Integration (Docker + Nginx + Raspberry Pi)

### Goal

Containerize server and frontend, run via Compose locally and on Raspberry Pi in Chromium kiosk. Vision/AI remain mocked.

### Output/Acceptance

- `docker compose up --build` serves SPA at `http://localhost` with working API proxy.
- On Pi, boot → kiosk opens → app loads; offline mocks still render; health checks pass.

### Steps

#### 3.1 Dockerfiles

**Backend (`mirror-server/Dockerfile`)**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY data ./data
EXPOSE 8080
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8080"]
```

Create `requirements.txt` with the libs from Guide 1 (omit heavy CV libs for mocks).

**Frontend (`mirror-frontend/Dockerfile`)**

```dockerfile
# build
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
# serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

#### 3.2 Compose (`ops/docker-compose.yml`)

```yaml
version: '3.9'
services:
  server:
    build: ../mirror-server
    ports: ['8080:8080']
    environment:
      - DATA_DIR=/app/data
      - PROVIDERS_WEATHER_MODE=mock
      - PROVIDERS_NEWS_MODE=mock

  web:
    build: ../mirror-frontend
    ports: ['80:80']
    depends_on: [server]
```

#### 3.3 Local Validation

```
cd ops
docker compose up --build
# Visit http://localhost
curl :8080/health
```

#### 3.4 Raspberry Pi Prep

- Raspberry Pi OS 64‑bit (`uname -m` → `aarch64`).
- Install Docker and compose plugin.
- Optional: use Buildx from dev box with `--platform linux/arm64` or build directly on Pi.

**Buildx example (from dev machine):**

```
docker buildx create --use --name sm-builder
# backend
docker buildx build --platform linux/arm64 -t <reg>/mirror-server:latest --push ../mirror-server
# frontend
docker buildx build --platform linux/arm64 -t <reg>/mirror-frontend:latest --push ../mirror-frontend
```

Update compose to `image:` instead of `build:` when deploying on Pi.

#### 3.5 Kiosk Setup

Create `ops/pi/kiosk.service`:

```
[Unit]
Description=Chromium Kiosk
After=network-online.target docker.service
Wants=network-online.target

[Service]
Environment=XDG_RUNTIME_DIR=/run/user/1000
User=pi
ExecStart=/usr/bin/chromium-browser --kiosk --incognito --noerrdialogs --disable-infobars \
  --check-for-update-interval=31536000 http://localhost
Restart=always

[Install]
WantedBy=graphical.target
```

Enable with `sudo systemctl enable kiosk && sudo systemctl start kiosk` (path may differ by distro).

#### 3.6 Pi Compose Deploy

On the Pi:

```
cd /opt/smart-mirror/ops
# If using images from registry
docker compose pull
docker compose up -d
curl :8080/health
```

#### 3.7 Offline/Resilience Checks

- Disconnect network: frontend remains usable; `/api/v1/morning-report` serves mock/stale values.
- Restart Docker or kill server: container restarts; kiosk reloads automatically.

**Completion Checklist**

- [ ] Local Compose serves SPA + API.
- [ ] Pi boots to kiosk showing the app.
- [ ] Health endpoint 200; todos persist across container restarts.
- [ ] App usable offline with clear stale indicators.
- [ ] Memory looks sane in `docker stats` (server ≤ ~300MB RSS; nginx small).

---

## Fast Follows (Vision & AI)

- Replace `snapshot.jpg` and WS mock with Picamera2 + MediaPipe/TFLite.
- Add `/vision/stream.mjpg` and real gesture intents.
- Add cloud LLM orchestration behind a flag for `POST /api/v1/voice/interpret`.

---

### Global Notes

- Keep secrets out of the repo; use `.env` files.
- Prefer simple logs (stdout). For Pi, avoid heavy log volumes.
- Document deviations and update `TEST_PLAN.md`.
