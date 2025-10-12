# Mira — Gesture Control Stack Guide (Mac + Raspberry Pi)

> A hands-on path to implement **video ingestion → gesture recognition → debounced commands** that flow into the Control Plane. This guide is learning‑oriented: start simple, get feedback on latency/accuracy, then harden.

---

## 0) What you’ll build

- A **gesture-worker** microservice that:
  1) Ingests video from **Mac webcam (dev)** or **Raspberry Pi camera (prod)**
  2) Runs fast, local inference (MediaPipe/TFLite) to extract **hand landmarks**
  3) Classifies **static** (palm, fist, point) and **dynamic** (swipe left/right) gestures
  4) Applies **debounce + state machine** to reduce false positives
  5) Emits **Commands** to the Mira **Control Plane** (Phase 2) via HTTP `/command` or Redis

**Target loop**: ≤ 50–80ms/frame on Mac; ≤ 120–160ms/frame on Pi 4/5 at 640×360.

---

## 1) Architecture (fits Phase 2 Control Plane)

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌────────────────────┐
│ Camera  │ ─→  │ Ingestion   │ ─→  │ Inference    │ ─→  │ Postproc / Classify │
│ (Mac/Pi)│     │  (OpenCV)   │     │ (MediaPipe)  │     │  + Debounce + FSM  │
└─────────┘     └─────────────┘     └──────────────┘     └────────────┬───────┘
                                                                      │
                                                         ┌─────────────▼─────────────┐
                                                         │ Emit Command → Control    │
                                                         │ Plane `/command` (HTTP)   │
                                                         │ or Redis Pub/Sub          │
                                                         └───────────────────────────┘
```

Key interfaces (from Phase 2):
- **Command** `{source:"gesture", action:"gesture_<name>", payload:{gesture, confidence, meta}}`
- Control Plane reduces to **StatePatch** and broadcasts via `/ws/state`.

---

## 2) Stack choices

**Inference baseline (recommended first):**
- **MediaPipe Hands (CPU)** — great for fast, robust hand landmarks; easy static + derived dynamic gestures.

**Alternatives (later):**
- **MediaPipe Holistic / Pose** for body‑based gestures
- **OpenVINO** or **PyTorch/TensorRT** for custom models

**Language:** Python 3.11 (aligns with existing FastAPI services)

---

## 3) Video ingestion (Mac vs. Raspberry Pi)

### 3.1 Mac (local dev)
- Dependencies: `pip install opencv-python mediapipe`
- Use the built-in camera via `cv2.VideoCapture(0)`
- Prefer smaller frames for latency: `640×360` or `960×540`; cap FPS ~30

**Snippet:**
```python
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
cap.set(cv2.CAP_PROP_FPS, 30)
```

### 3.2 Raspberry Pi (production)
**Option A: Picamera2 → NumPy → OpenCV** (simplest)
- `sudo apt install -y python3-picamera2 libatlas-base-dev`
- Python: `pip install mediapipe opencv-python` (or `opencv-python-headless` if no GUI)

**Option B: GStreamer pipeline into OpenCV** (tunable)
- Example pipeline (IMX/CSI cameras vary):
```
cv2.VideoCapture(
  "libcamerasrc ! video/x-raw, width=640, height=360, framerate=30/1 ! \
   videoconvert ! video/x-raw,format=BGR ! appsink", cv2.CAP_GSTREAMER)
```

**Performance tips:**
- Disable desktop compositing on Pi for kiosk to free CPU
- Use `cv2.cvtColor` sparingly; keep BGR input where possible
- Downscale early (`cv2.resize`) before inference

---

## 4) Minimal working example (hand landmarks + HUD)

> Start here. Verify inference speed and stability before adding gestures.

```python
import cv2, time
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)  # switch to Pi pipeline in prod
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
cap.set(cv2.CAP_PROP_FPS, 30)

with mp_hands.Hands(model_complexity=0, max_num_hands=1,
                     min_detection_confidence=0.4,
                     min_tracking_confidence=0.4) as hands:
    prev = time.time()
    while True:
        ok, frame = cap.read()
        if not ok: break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = hands.process(rgb)
        if res.multi_hand_landmarks:
            for hand in res.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
        # FPS HUD
        now = time.time(); fps = 1.0 / (now - prev); prev = now
        cv2.putText(frame, f"FPS: {fps:.1f}", (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        cv2.imshow('gesture-dev', frame)
        if cv2.waitKey(1) & 0xFF == 27: break  # ESC to exit
cap.release(); cv2.destroyAllWindows()
```

**Goal checks:** FPS ≥ 20 on Mac, ≥ 12 on Pi at 640×360.

---

## 5) Static gesture classification (palm / fist / point)

Approach: compute **finger openness** by comparing tip vs. knuckle vectors relative to the wrist. A quick heuristic:
- For each finger, if (tip_y < pip_y) in image coordinates when hand is upright → **extended**
- Build bitmask: thumb/index/middle/ring/pinky → map to labels

**Pseudo:**
```python
mask = (thumb_open<<4) | (index_open<<3) | (middle_open<<2) | (ring_open<<1) | pinky_open
label = {0b11111:'palm', 0b00000:'fist', 0b10000:'point'}
```

Refine later with angles (cosine between joints) to be rotation‑invariant.

---

## 6) Dynamic gesture (swipe left/right)

Idea: track **hand centroid x** over a short **temporal buffer** (e.g., last 300–500ms). If net Δx exceeds a threshold and velocity is consistent → emit `swipe_*`.

**Steps:**
1) For each frame, compute centroid `cx` from landmarks (average x of visible points)
2) Append `(t, cx)` to deque; keep ~15 frames at 30 FPS
3) Compute `dx = cx[t_now] - cx[t_old]`; if `|dx| > SWIPE_PIXELS` and stddev of velocity small → candidate
4) Combine with **static** openness (e.g., palm open) to reduce false positives

**Heuristic constants (start):**
- `SWIPE_PIXELS ≈ 120 @ 640px width`
- `MAX_WINDOW_MS ≈ 400`
- Require **one open palm**

---

## 7) Debounce + Finite State Machine (FSM)

Goals: avoid rapid toggling and idle noise.

**States:** `IDLE → ARMED → TRIGGERED → COOLDOWN → IDLE`
- Enter **ARMED** when confidence > `0.6` for `≥ 120ms`
- **TRIGGERED** when classification stable for `≥ 100ms`
- **COOLDOWN** hold `300ms` to ignore repeats

**Confidence:** combine model score (MediaPipe tracking conf) + heuristic margin (e.g., movement magnitude / threshold)

Emit at most **1 command per gesture** per cooldown window.

---

## 8) Emitting Commands → Control Plane

HTTP (simplest to start):
```python
import httpx, time, uuid

async def emit(action, payload, url="http://localhost:8090/command"):
    cmd = {
      "id": str(uuid.uuid4()),
      "ts": time.strftime('%Y-%m-%dT%H:%M:%S'),
      "source": "gesture",
      "action": action,
      "payload": payload
    }
    async with httpx.AsyncClient() as c:
        r = await c.post(url, json=cmd)
        r.raise_for_status()
```

Examples:
- `gesture_palm` → toggle HUD overlay
- `gesture_swipe_left` → navigate page left
- Include `{gesture, confidence, dwell_ms}` in payload

Later: publish directly to **Redis** if you want lower overhead.

---

## 9) Putting it together (worker skeleton)

```python
# gesture_worker.py
import asyncio, time, collections, numpy as np
import cv2, mediapipe as mp
from math import sqrt
from typing import Deque, Tuple
from httpx import AsyncClient

class GestureWorker:
  def __init__(self, src=0, width=640, height=360):
    self.cap = cv2.VideoCapture(src)
    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    self.hands = mp.solutions.hands.Hands(model_complexity=0, max_num_hands=1,
                    min_detection_confidence=0.4, min_tracking_confidence=0.4)
    self.buf: Deque[Tuple[float,float]] = collections.deque(maxlen=16)
    self.cool_until = 0

  def centroid_x(self, lm):
    xs = [p.x for p in lm.landmark]
    return np.mean(xs)

  def label_static(self, lm):
    # naive index-open check as example
    idx_tip = lm.landmark[8].y; idx_pip = lm.landmark[6].y
    mid_tip = lm.landmark[12].y; mid_pip = lm.landmark[10].y
    ring_tip = lm.landmark[16].y; ring_pip = lm.landmark[14].y
    pink_tip = lm.landmark[20].y; pink_pip = lm.landmark[18].y
    opens = [idx_tip < idx_pip, mid_tip < mid_pip, ring_tip < ring_pip, pink_tip < pink_pip]
    if all(opens): return 'palm'
    if not any(opens): return 'fist'
    if opens[0] and not any(opens[1:]): return 'point'
    return 'other'

  async def emit(self, action, payload):
    async with AsyncClient() as c:
      await c.post("http://localhost:8090/command", json={
        "source":"gesture","action":action,"payload":payload
      })

  async def run(self):
    prev = time.time()
    while True:
      ok, frame = self.cap.read()
      if not ok: break
      rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
      res = self.hands.process(rgb)
      now = time.time()
      if res.multi_hand_landmarks:
        lm = res.multi_hand_landmarks[0]
        cx = self.centroid_x(lm)  # 0..1
        self.buf.append((now, cx))
        label = self.label_static(lm)
        # dynamic swipe
        if len(self.buf) >= 8 and now > self.cool_until and label=='palm':
          t0, x0 = self.buf[0]; t1, x1 = self.buf[-1]
          dx = (x1 - x0)  # normalized
          dur = (t1 - t0)
          if dur > 0.18 and abs(dx) > 0.18:  # thresholds to tune
            action = 'gesture_swipe_right' if dx > 0 else 'gesture_swipe_left'
            self.cool_until = now + 0.35
            await self.emit(action, {"gesture": action, "dx": dx, "dur": dur, "confidence": min(1.0, abs(dx)/0.3)})
      # small sleep yields CPU
      await asyncio.sleep(0)

if __name__ == "__main__":
  asyncio.run(GestureWorker().run())
```

Run this with the Control Plane up. Watch `/ws/state` in the frontend HUD to confirm StatePatches are applied.

---

## 10) Diagnostics & UX

- **On‑frame overlay**: draw centroid, path trail, and current label + confidence
- **Console logs**: print gesture candidates with dx/dur for tuning
- **Frontend HUD**: show last gesture, confidence, and cooldown timer

---

## 11) Latency & accuracy tuning checklist

- Resolution: 640×360 → 480×270 if needed
- Model params: lower `model_complexity` and `max_num_hands=1`
- Thresholds: start loose, tighten after observing real traces
- Lighting: ensure even face/hand lighting; avoid backlight
- Camera placement: consistent framing; prefer chest‑to‑waist height so hands enter the same region

---

## 12) Packaging & deployment

**Dockerfile (worker):**
```
FROM python:3.11-slim
RUN apt-get update && apt-get install -y libglib2.0-0 libgl1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python","gesture_worker.py"]
```
`requirements.txt`: `opencv-python-headless\nmediapipe\nhttpx`

Compose add‑on:
```
  gesture-worker:
    build: ../gesture-worker
    depends_on: [control-plane]
    devices:  # on Pi if using /dev/video0
      - "/dev/video0:/dev/video0"
```

On Pi using Picamera2, you may not expose `/dev/video0`; instead run worker on the host or use libcamerasrc → GStreamer pipeline.

---

## 13) Test plan

1) **Dry run (Mac)**: palm swipes left/right; confirm commands created in Control Plane `events` table
2) **Edge cases**: partial occlusion, fast flicks, background motion
3) **False positive audit**: 5‑minute idle run; goal: **0** unintended triggers
4) **Replay**: record short MP4s; build a file‑source mode to run the worker on recordings for deterministic tuning

---

## 14) Next steps / Fast follows

- Add **gesture confidence policy**: require ≥0.7 to affect navigation; else request confirmation (voice or timeout)
- Expand gesture set: **palm** (open menu), **fist** (close), **point** (cursor mode)
- Move from HTTP to **Redis** emit for lower latency
- Consider **two‑hand gestures** for privileged actions (reduce accidental triggers)
- Persist per‑user thresholds in SQLite via App API settings

---

## 15) Reference points in Mira docs

- Phase 1 mock vision WS and preview (baseline HUD)
- Phase 2 Control Plane schemas and `/command` endpoint
- Compose layout with `app-api`, `control-plane`, `web`, and (now) `gesture-worker`

> With this guide, you can iterate in tight loops: start on Mac, hit your FPS, validate swipes, then push to Pi and adjust thresholds for your camera and lighting. Keep logs of dx/dur thresholds per environment to converge quickly.

