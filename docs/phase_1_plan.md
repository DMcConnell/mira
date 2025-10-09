# Mira – Phase 1 Agent Guide

> **Goal:** Ship a Raspberry Pi–hosted smart mirror MVP that boots into a Chromium kiosk, serves a web UI, and supports: Morning Report (Calendar/Weather/News/To‑Dos), mode switching (Morning/Ambient), text-based “voice” commands, and **Vision Phase 1** (camera online, low-latency stream, minimal gesture intents). This guide is self‑contained for an agent/intern to implement independently.

---

## 0) Definition of Done (DoD)

- Pi powers on → Chromium kiosk auto-opens the local web app.
- Morning Report renders with mock data offline and live data when configured; stale states are visibly labeled.
- Mode switching (Morning/Ambient) works with a smooth transition.
- Text command stub executes intents: `switch to ambient`, `add todo <text>`.
- **Vision P1:** camera is detected; live preview available; minimal gesture set emits intents with on-screen confirmation and debouncing.
- One-command local bring-up via Docker Compose; one-command Pi deploy.
- Memory within targets: server ≤ ~350MB RSS; Chromium 400–700MB; nginx minimal. Verified via `docker stats`.
- Docs present: `README.md`, `DEPLOY_PI.md`, `TEST_PLAN.md`, `OPERATIONS.md`.

**Validation summary**

- Local: `docker compose up --build` → open `http://localhost` → verify all panels and gestures HUD work.
- Pi: Power cycle → kiosk launches → run curl health checks → confirm camera stream and gestures → record memory numbers.

---

## 1) Architecture

- **Frontend:** React + Vite + TypeScript, TailwindCSS, Framer Motion (served as static files by nginx).
- **Server:** FastAPI (REST + WebSocket). Includes providers (weather/news/calendar), todos persistence, settings, and AI/text-intent endpoint.
- **Vision:** Picamera2 + TFLite/MediaPipe in-process module (within the server) _or_ sibling module in same container. Emits intents over internal queue and WS.
- **Runtime:** Docker Compose; arm64 images; Chromium kiosk points to `http://localhost`.

**APIs (v1)**

- `GET /health` → `{ status: "ok" }`
- `GET /api/v1/morning-report` → `{ calendar:[], weather:{...}, news:[], todos:[] }`
- `GET|POST|PUT|DELETE /api/v1/todos`
- `POST /api/v1/voice/interpret` → `{ intent, args }`
- `WS /ws/vision` (server → FE): `{ ts, gesture, confidence, armed }`
- `POST /api/v1/vision/arm` / `POST /api/v1/vision/disarm`
- `GET /api/v1/settings` / `PUT /api/v1/settings`

**DTOs**

- `CalendarItem { id, title, startsAtISO, endsAtISO, location? }`
- `WeatherSnapshot { updatedISO, tempC, condition, icon, stale }`
- `NewsItem { id, title, source, url, publishedISO }`
- `Todo { id, text, done, createdAtISO }`
- `VisionIntent { tsISO, gesture, confidence, armed }`

---

## 2) Repo Layout

```
smart-mirror/
  mirror-frontend/          # React/Vite/TS
  mirror-server/            # FastAPI + Vision
    app/
      api/                  # morning_report.py, todos.py, settings.py, health.py, voice.py
      vision/               # camera.py, gestures.py, pipeline.py
      providers/            # weather.py, news.py, calendar.py (mock/live toggle)
      models/               # pydantic DTOs
      ws/                   # websocket endpoints & broadcaster
    main.py
  ops/
    docker-compose.yml
    env/.env.example
    pi/ (kiosk.service, install_kiosk.sh)
  docs/
    README.md
    DEPLOY_PI.md
    TEST_PLAN.md
    OPERATIONS.md
  contracts/
    openapi.json (exported)
```

**Validation**: Dir tree matches; `uvicorn app.main:app` runs locally and exposes `/docs`.

---

## 3) Development Environment

- Node 20+, pnpm/npm; Python 3.11; Docker + Buildx; Make (optional).
- Python deps: `fastapi`, `uvicorn[standard]`, `pydantic`, `jinja2` (if needed), `httpx`, `picamera2`, `opencv-python-headless`, `mediapipe` _or_ `tflite-runtime` (choose one path below).

**Validation**: `python -c "import fastapi, cv2; print('ok')"` prints `ok`.

---

## 4) Frontend (React/Vite/TS)

### 4.1 Structure

```
src/
  app/
  components/ (Card, Quadrant, ModeSwitcher, Toast)
  features/{calendar,weather,news,todos,vision}
  lib/api/ (OpenAPI-generated client optional)
  styles/tailwind.css
```

### 4.2 Features

- Quadrant dashboard panels + skeleton loaders.
- Hidden **Settings** (keyboard shortcut) showing provider modes, version hash, data timestamps, and vision status.
- Mode switcher with subtle Framer Motion transitions.
- Text command modal → calls `/api/v1/voice/interpret`.
- Vision HUD (small overlay): `armed`, `confidence`, FPS.
- Camera preview element: `<img src="/vision/stream.mjpg">` **or** `<video>` bound to a WS/MediaSource stream.

**Validation**

- With server in mock mode, panels render.
- Typing `add todo buy milk` adds an item.
- Vision HUD updates when camera on; preview visible.

---

## 5) Server (FastAPI)

### 5.1 Config & Flags

- Env vars:
  - `PROVIDERS_WEATHER_MODE=mock|live`
  - `PROVIDERS_NEWS_MODE=mock|live`
  - `CAMERA_ENABLED=true|false`
  - `VISION_MIN_CONFIDENCE=0.8`
  - `VISION_WAKE_HOLD_MS=500`
  - `VISION_FPS=12`
  - `VISION_RESOLUTION=640x480`

### 5.2 Providers

- Each provider exposes `get_*()`; in mock mode returns deterministic sample data; in live mode caches last good response and marks `stale` if expired or unreachable.

### 5.3 Todos

- JSON file persistence: `data/todos.json` with atomic writes.

### 5.4 Voice (text intent)

- Regex-based interpreter for `switch to (ambient|morning)` and `add todo (.*)`; else `unknown`.

### 5.5 Vision P1

- **Capture**: Picamera2 in video mode @ `VISION_FPS`, `VISION_RESOLUTION`.
- **Processing**: choose one path
  - **MediaPipe Hands**: get 21 landmarks → small rule-based gesture classifier.
  - **TFLite**: hand detector + landmark model + tiny softmax classifier.
- **Gestures (minimal set)**
  - **Wake**: Open palm for `VISION_WAKE_HOLD_MS` → `armed=true`.
  - **Swipe Left / Swipe Right**: Navigation intents when `armed`.
  - **Fist (Hold 300ms)**: Confirm/select.
  - **Palm (Hold 300ms)**: Back/cancel.
- **Smoothing**: majority vote over last `K=5` frames; debounce ≥300ms per same intent.
- **Output**: broadcast `VisionIntent` over `WS /ws/vision`; optional HTTP hook `/api/v1/vision/intent` (for server-side effects).
- **Preview**: MJPEG endpoint `/vision/stream.mjpg` (multipart/x-mixed-replace) and `/vision/snapshot.jpg`.

**Validation**

- `libcamera-hello --list-cameras` lists module.
- `curl :8080/vision/snapshot.jpg` returns a valid JPEG.
- FE receives WS messages with changing `confidence` when hand enters ROI.
- Swipe gestures trigger UI navigation only when `armed=true`.

---

## 6) Dockerization & Compose

### 6.1 Server Image

- Base: `python:3.11-slim` (arm64 available).
- Install OS libs for Picamera2/OpenCV as needed; keep image small.
- Expose 8080; run `uvicorn app.main:app --host 0.0.0.0 --port 8080`.

### 6.2 Frontend Image

- Build Vite → copy `dist/` into `nginx:alpine` at `/usr/share/nginx/html`.

### 6.3 Compose File (`ops/docker-compose.yml`)

```yaml
services:
  server:
    build: ../mirror-server
    ports: ['8080:8080']
    environment:
      - PROVIDERS_WEATHER_MODE=${PROVIDERS_WEATHER_MODE:-mock}
      - PROVIDERS_NEWS_MODE=${PROVIDERS_NEWS_MODE:-mock}
      - CAMERA_ENABLED=${CAMERA_ENABLED:-true}
      - VISION_MIN_CONFIDENCE=${VISION_MIN_CONFIDENCE:-0.8}
      - VISION_WAKE_HOLD_MS=${VISION_WAKE_HOLD_MS:-500}
      - VISION_FPS=${VISION_FPS:-12}
      - VISION_RESOLUTION=${VISION_RESOLUTION:-640x480}
    devices:
      - '/dev/video0:/dev/video0'
    deploy:
      resources:
        limits:
          memory: 350m

  web:
    build: ../mirror-frontend
    ports: ['80:80']
    depends_on: [server]
```

**Validation**

- `docker compose up --build` → `http://localhost` loads.
- `docker stats` shows memory within targets.

---

## 7) Raspberry Pi Setup & Kiosk

### 7.1 Pi Essentials

- Raspberry Pi OS 64‑bit; confirm `uname -m` → `aarch64`.
- Install Docker & Compose plugin.
- Enable cgroups: add `cgroup_enable=cpuset cgroup_enable=memory cgroup_memory=1` to `/boot/cmdline.txt`.

### 7.2 Kiosk Service

- Install Chromium.
- `kiosk.service` (systemd) launches:

```
/usr/bin/chromium-browser --kiosk --incognito --noerrdialogs --disable-infobars \
  --check-for-update-interval=31536000 http://localhost
```

**Validation**

- Reboot → kiosk opens to the app.
- Network unplugged → app still renders mock data; weather/news marked stale.

---

## 8) Observability & Ops

- `/health` 200 when all sub-systems OK; include camera status in payload.
- Vision logs: FPS, dropped frames, avg inference time, false-positive counter.
- FE Settings shows version hash, provider modes, vision state (armed/idle), and last WS message ts.

**Validation**

- Kill camera process; UI shows “gestures offline,” manual controls work; process auto-restarts.

---

## 9) Security & Privacy

- Local-only processing of frames; no frame storage by default.
- On-screen indicator when camera active.
- Optional debug ring buffer (≤5 s) is **off by default**; if enabled, auto-purge and never written to disk in default config.

**Validation**

- Repo search reveals no hard-coded secrets; `.env` drives all keys/flags.

---

## 10) Performance Targets & Tuning

- Vision: 10–15 FPS, median intent latency ≤150 ms, p95 ≤250 ms.
- CPU: vision ≤60% of one core at target FPS; server total RSS ≤350MB.
- FE: 60 FPS animations on Pi; avoid heavy filters/shadows; memoize expensive components.

**Validation**

- Metrics endpoint or logs confirm FPS and latency; visual smoothness acceptable on-device.

---

## 11) Acceptance Tests (copy to TEST_PLAN.md)

**Functional**

1. Morning Report loads; each panel shows data or clear “stale” fallback.
2. Text: `switch to ambient` flips mode; `add todo buy milk` adds item.
3. Vision: holding an open palm in the interaction box for ≥`VISION_WAKE_HOLD_MS` arms the system.
4. Swipes (L/R) navigate; Fist = confirm; Palm = back; all require `armed=true` and show a confirmation flash.

**Performance** 5. Intent latency p95 ≤250 ms over 100 trials. 6. CPU and memory targets met under `docker stats` for ≥10 minutes idle + 10 minutes active use.

**Resilience** 7. Disconnect/reconnect camera: preview and gestures recover without full reboot. 8. Stop network: app remains usable; panels degrade gracefully.

**Privacy** 9. No image/video files exist after usage; logs contain only aggregate metrics and gesture labels.

---

## 12) Optional Enhancements (not required for DoD)

- WebRTC preview to reduce latency and bandwidth.
- Coral USB TPU path (compile compatible models) if FPS/latency fails targets.
- ICS calendar ingest (read-only) without OAuth.
- Systemd watchdog for kiosk and server.

---

## 13) Quick Commands

- **Local run:** `docker compose -f ops/docker-compose.yml up --build`
- **Health:** `curl :8080/health`
- **Snapshot:** `curl :8080/vision/snapshot.jpg -o /tmp/snap.jpg`
- **Text intent:** `curl -X POST :8080/api/v1/voice/interpret -H 'Content-Type: application/json' -d '{"text":"switch to ambient"}'`
- **Metrics:** `docker stats`

---

**Implement exactly as written.** Capture deviations in PRs and update `TEST_PLAN.md` accordingly.
