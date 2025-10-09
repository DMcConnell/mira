# Project Mira — Development Roadmap & Architecture Plan

## 1. Vision Overview

**Project Mira** is a renter-compatible, AI-powered smart mirror that acts as a personalized daily dashboard and conversational assistant.  
It blends local hardware (Raspberry Pi, camera, microphone, display) with lightweight cloud-based AI, supporting both **voice** and **gesture** control through a modular software architecture.

Mira’s long-term goal is a portable, privacy-respecting device that enhances daily life with actionable, glanceable insights — calendar, weather, news, and tasks — and that can expand into health, finance, and smart-home control.

---

## 2. Core Design Principles

1. **AI-first Interaction** — hands-free voice and gesture input; conversational UX.  
2. **Bidirectional Control Loop** — the Control Plane arbitrates all commands and state updates before anything reaches the UI.  
3. **Separation of Concerns** — distinct modules for Control Plane (real-time loop) and App API (CRUD/config).  
4. **Portability** — renter-safe build; mirror hardware detachable and reusable.  
5. **Privacy & Locality** — local audio/video processing with optional cloud fallback.  
6. **Extensibility** — additional frontends (e.g., phone controller) can securely toggle sensors or modes.

---

## 3. High-Level Architecture (Middle-Tier Implementation)

| Layer | Responsibility | Technology |
|-------|----------------|-------------|
| **Control Plane** | Real-time loop handling commands, policy, events, and state; orchestrates device workers (mic, camera, gesture). | FastAPI + asyncio + Redis + SQLite |
| **App API** | User profiles, widgets, and historical data; reads event log from Control Plane. | FastAPI + SQLite |
| **UI Layer** | React/Vite SPA for Mirror display and phone controller; WebSocket bi-directional updates. | React + TypeScript + Tailwind |
| **Device Workers** | Hotword, ASR, Gesture; run as internal async tasks or light sidecars. | Python subprocesses or threads |
| **Infra** | Docker Compose on Raspberry Pi; Redis for pub/sub; optional kiosk mode via Chromium. | Docker + Systemd |

**Key Concepts**
- **Command → Policy → Event → StatePatch** pipeline ensures determinism.  
- **SQLite** persists events and snapshots.  
- **Redis Pub/Sub** broadcasts state patches to multiple UIs.  
- **Security:** shared PIN → short-lived JWT → capability flags (`mic.toggle`, `cam.toggle`).  

---

## 4. Development Roadmap

### **Phase 1 — MVP Software (Done per guides)**

Focus: functional software prototype, mocked AI/vision.

**Deliverables**
- Backend ( FastAPI ) with REST + WS:
  - `/health`, `/api/v1/morning-report`, `/api/v1/todos`, `/api/v1/voice/interpret`, `/api/v1/settings`
  - WS `/ws/vision` (mock gesture intents)
- Frontend ( React/Vite/TS ) SPA:
  - Morning Report dashboard (Calendar | Weather | News | Todos)
  - Mode switcher, text command modal, hidden settings drawer
  - WS HUD for mock gestures
- Integration (Docker + Pi):
  - Compose stack (`web`, `server`)
  - Chromium kiosk boot service
- Unit tests, health checks, offline resilience.

**Outcome:** fully usable software mirror running locally or on Pi, with mocked AI subsystems.

---

### **Phase 2 — Control Plane & Real-Time Event Loop**

Focus: implement bidirectional control architecture and solidify device orchestration.

**Goals**
- Add Control Plane process (FastAPI + Redis + SQLite)
- Formalize Command/Event/StatePatch schema
- Implement:
  - **Arbiter task** (policy + reducer)
  - **Broadcaster task** (Redis pub/sub → WS clients)
  - **Device workers** (mic hotword, fake gesture) producing commands
- Persist events/snapshots in SQLite (`events`, `snapshots` tables)
- Replace mock WS HUD with real event stream.
- Simple PIN → JWT handshake for frontends.

**Deliverables**
- Running 2-service Compose: `control-plane`, `app-api`
- Shared Redis + SQLite volume
- Updated frontend WS connection to receive real StatePatches

---

### **Phase 3 — Hardware Integration**

Focus: physical mirror assembly + basic vision.

**Goals**
- Build mirror enclosure (two-way glass + Pi + display)
- Integrate camera and microphone
- Replace mocks with:
  - Picamera2 + MediaPipe gesture model
  - Local hotword + VAD for wake/command mode
- Wire physical LEDs or on-screen indicators for mic/cam state
- Deploy full Compose stack on Pi with kiosk auto-start.

**Deliverables**
- Wall-mounted prototype mirror
- Working gesture controls for mode switching or page navigation
- Reliable hotword activation with voice commands

---

### **Phase 4 — Cloud AI & Smart-Home Expansion**

Focus: bring true AI and external integrations online.

**Goals**
- Integrate Bedrock or OpenAI LLM for real conversational control
- Extend voice intents beyond static regex
- Add Smart-Home Lite:
  - Wi-Fi bulbs and plugs (portable devices only)
  - Mirror UI toggles via Control Plane
- Add Finance and Health dashboards (API integrations)
- Logging & metrics enhancements.

**Deliverables**
- Hybrid local/cloud AI orchestration
- Expanded dashboard suite
- Secure remote phone controller (HTTPS, capability-scoped tokens)
- Telemetry dashboard for debugging latency and resource use

---

### **Phase 5 — Polish, Learning, and Packaging**

Focus: stability, self-learning, distribution.

**Goals**
- Event-replay recovery and snapshot auto-save
- Lightweight analytics (frequency of commands, gesture accuracy)
- User routines learning (time-based suggestions)
- OTA update mechanism
- Optional open-source packaging and build scripts.

**Deliverables**
- Stable, distributable image for Raspberry Pi 4 / 5
- Documentation set: build guide, developer API, architecture diagram
- Demo video & usage walkthrough

---

## 5. Key Risks & Mitigations

| Risk | Mitigation |
|------|-------------|
| **AI latency or cloud outages** | Local fallback and cached responses. |
| **Gesture false positives** | Confidence thresholds + policy confirmation (voice or timeout). |
| **Power or Pi performance limits** | Optimize refresh rates; offload heavy inference. |
| **Security surface for remote control** | Capability-scoped JWTs + LAN binding by default. |
| **Display visibility through mirror film** | Prototype both glass and film; calibrate brightness. |

---

## 6. Deliverable Summary

| Phase | Output | Deployment |
|-------|---------|------------|
| **1** | Mocked full-stack MVP (backend, frontend, compose) | Local + Pi |
| **2** | Real-time Control Plane, Redis/SQLite infra | Local + Pi |
| **3** | Hardware build, real gestures + mic | Physical mirror |
| **4** | Cloud AI, smart-home expansion | Hybrid deployment |
| **5** | Final polish, OTA, packaging | Public image |

---

## 7. Next Step

Proceed with **Phase 2 implementation**:  
Set up `control-plane/` per the middle-tier architecture, integrate Redis + SQLite, and refactor the existing FastAPI mock backend to delegate commands/events through the Control Plane.
