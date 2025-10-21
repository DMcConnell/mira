# Mira MVP — Hands‑Free UI/UX Plan

Last updated: 2025-10-21 03:12

## 0) Executive Summary

Mira is a hands‑free, voice‑ and gesture‑controlled ambient assistant running on a mirror/monitor. The MVP focuses on a reliable global vs in‑app navigation model, a robust debug overlay, strict **Public vs Private** privacy modes, and a minimal set of apps that prove the interaction loop: **Home**, **Weather**, **Email**, **Finance**, **News**, **Todos**, **Calendar** (with **Commute** as a reach goal).

Key decisions:

- **No touch/typing**; all interactions via **voice + gestures**.
- **Two-hand modifier model** distinguishes **Global Navigation (GN)** from **In‑App Navigation (IAN)** and **either hand** can act as the modifier.
- **Public Mode defaults** on wake and hides sensitive apps entirely (no partial redaction). **Settings are fully visible in Public Mode**.
- **Debug Overlay** can be enabled via voice and shows camera + landmarks + gesture/ASR diagnostics.

---

## 1) Interaction Model

### 1.1 Control Layers

- **Global Navigation (GN):** App switching and system actions (Home/Settings/Mode toggles).
- **In‑App Navigation (IAN):** Move/scroll/select within the active app.

### 1.2 Two‑Hand Modifier (either hand works)

- **GN armed** when **one hand is steady & open** (≥ 250 ms) and **the other** performs a gesture.
- If both hands gesture (no steady open hand), interpret as **In‑App** to avoid accidental global actions.
- Hysteresis of ~120 ms to prevent flicker.

### 1.3 Base Gestures

- **Open palm (steady):** arm GN (when other hand gestures) / show HUD pulse.
- **Swipe Left/Right:** previous/next (GN when armed, else IAN).
- **Pinch (tap):** select/confirm.
- **Fist (tap):** back/cancel.
- **Two‑finger hold:** quick actions.
- **Dwell:** select after **700 ms** (tuneable; default ON).

### 1.4 Voice Intents (short)

- **Apps:** “open weather / email / finance / news / todos / calendar / settings / home”
- **Nav:** “next”, “previous”, “back”, “select”, “read that”, “details”
- **System:** “Mira enable debug overlay”, “Mira disable debug”, “Mira private mode <code>”, “Mira public mode”, “mic off/on”, “camera off/on”
- **Wake:** any phrase containing **“Mira”** (wake phrase is easily configurable).

---

## 2) Privacy Modes

### 2.1 Modes

- **Public (default on wake):** hide sensitive apps entirely from the rail and routes.
- **Private (explicit voice):** “Mira private mode <code>”. Exit via “Mira public mode” or idle timeout (default 5 min).

### 2.2 App Visibility by Mode

- **Public:** Show **Home, Weather, News, Todos, Calendar (Today title list), Settings**. **Email and Finance are not shown at all** (hidden from rail and routes).
- **Private:** All apps fully visible.
- **Settings:** fully visible in both modes.

### 2.3 Indicators

- Corner **privacy chip**: Public (hollow icon) vs Private (solid lock) with color tint.
- Optional soft sound cue on enter/exit.

---

## 3) Debug Overlay (voice‑toggled)

- **Camera preview** with MediaPipe hand landmarks, pose labels, FPS.
- **Gesture stream**: last frames (pose/velocity/confidence).
- **Mode/State**: GN/IAN, `appRoute`, `focusPath`, `ui.mode`.
- **Reducer timings**: gesture→intent ms; intent→statePatch ms; WS latency.
- **Voice**: wake hits, last ASR/intent + confidence.
- **Dwell visualizer** on focus target.
- **Privacy banner** indicating current mode’s policy.

---

## 4) UI Shell

### 4.1 Home (Quadrant Dashboard)

- Tiles: Calendar | Weather | News | Todos (large, voice‑addressable).

### 4.2 App Rail

- Appears only when **GN is armed**; order: `[Home, Weather, Email, Finance, News, Todos, Calendar, Settings]`.
- In **Public Mode**, **Email/Finance are omitted** from the rail entirely.

### 4.3 Focus & Feedback

- High‑contrast **focus ring** with subtle pulse; dwell‑fill ring for 700 ms.
- HUD chips: mic, cam, WS, privacy, debug.

---

## 5) App Contracts

```ts
interface MiraApp {
  id:
    | 'home'
    | 'weather'
    | 'email'
    | 'finance'
    | 'news'
    | 'todos'
    | 'calendar'
    | 'settings';
  onFocus(path: string[]): void;
  handle(
    cmd:
      | { type: 'app.navigate'; payload: 'next' | 'prev' }
      | { type: 'app.selectFocus' }
      | { type: 'app.quickActions' }
      | { type: 'read.aloud' | 'details' },
  ): void;
  render(ui: UIState): VNode;
}
```

**Calendar (MVP):** Today list (time•title•location), detail view, “read that”.  
**Commute (reach):** Read‑only “Leave by HH:MM” tile; later live data.

---

## 6) State & Commands

### 6.1 UI & Sensors (types)

```ts
type UIState = {
  mode: "public"|"private",
  appRoute: "home"|"weather"|"email"|"finance"|"news"|"todos"|"calendar"|"settings",
  focusPath: string[],
  gnArmed: boolean,
  debug: { enabled: boolean },
  hud: { micOn: boolean, camOn: boolean, wsConnected: boolean, wake: boolean },
  confirm?: { text: string, action: Command, expiresAt: number }
}

type SensorsState = {
  hands: Record<string, {
    present: boolean,
    pose: "open"|"fist"|"pinch"|"twoFinger"|"unknown",
    velocity: { x:number, y:number, mag:number },
    steadyMs: number
  }>>,
  voice: { heardWake: boolean, intent?: Intent, transcript?: string, confidence?: number },
  perf: { fps: number, latencies: { reducerMs:number, wsMs:number } }
}
```

### 6.2 Context & Mapping

```ts
// GN context (either hand can be the modifier)
gnArmed = (exists steady open hand ≥ 250ms) AND (other hand performing a gesture)

// Gesture → Command
GN:    swipe→ nav.nextApp / nav.prevApp; pinch→ nav.openAppFocused; fist→ nav.backOrHome
IAN:   swipe→ app.navigate(next|prev);    pinch/dwell→ app.selectFocus; twoFinger→ app.quickActions
```

### 6.3 Public Mode Router

- When `ui.mode === "public"`, Email and Finance apps are completely removed from the app registry, rail, and routing. Voice commands and gestures cannot reference them. The system behaves as if these apps do not exist, preventing any discovery that private apps are available.

---

## 7) Configuration (defaults)

- `WAKE_KEYWORD="mira"` (regex word boundary; case‑insensitive; hot‑swappable).
- `DWELL_MS_DEFAULT=700` (tuneable; default ON).
- `GN_STEADY_MS=250`, `GN_HYSTERESIS_MS=120`.
- `PRIVACY_IDLE_TIMEOUT_MS=300000` (5 min).
- `PRIVATE_CODE="<set via env/local store>"`.

---

## 8) Implementation Plan (Segmented Steps)

### Phase A — Spec & Scaffolding

1. **Lock constants & env** (wake keyword, dwell, private code).
2. **Mediapipe reducer**: normalize hands → poses/velocity/steadyMs; detect swipe/pinch/fist/two‑finger/dwell.
3. **Context detector**: compute `gnArmed` with hysteresis.
4. **Command router**: merge gesture & voice; confirmations for low‑confidence destructive actions.
5. **Public/Private policy**: route guard + app registry that filters by mode.

**Exit Criteria:** Commands emitted correctly in logs; hidden apps filtered in Public.

### Phase B — UI Shell & Debug

6. **App Rail** (GN‑only visibility) + **HUD chips**.
7. **Focus ring** + dwell visualizer.
8. **Debug Overlay**: camera+landmarks, gesture/ASR, timing, privacy banner.

**Exit Criteria:** End‑to‑end WS state patches render; overlay toggles via voice.

### Phase C — Core Apps (MVP)

9. Refactor **Home/Weather/News/Todos** to `MiraApp` contract.
10. Implement **Email** (list + read‑aloud) — hidden in Public.
11. Implement **Finance** (snapshot + chart) — hidden in Public.
12. Implement **Calendar** (Today list + detail + read‑aloud).

**Exit Criteria:** “Open/Next/Back/Select/Read” loop works across visible apps; hidden apps are inaccessible in Public.

### Phase D — Privacy & Calibration

13. **Private Mode** voice flow with code; chip indicators; idle timeout.
14. **Calibration**: palm size/distance; store per‑user offsets.

**Exit Criteria:** Mode switching reliable; thresholds feel reasonable for the user.

### Phase E — Device & Stability

15. **Kiosk/RPi compose**; auto‑start; offline snapshot restore.
16. **Usability runs** with scripted scenarios; tune thresholds.

**Exit Criteria:** 10‑minute demo without failures; logs clean (no oscillation).

### Phase F — (Reach) Commute Tile

17. Mock route input & “Leave by” suggestion; later integrate live source.

**Exit Criteria:** Tile renders and responds to “open commute / details”.

---

## 9) Acceptance Tests (Hands‑Free Scenarios)

- **AT‑01:** "Mira open weather → next → details → back → home". Pass if all without touch.
- **AT‑02:** GN swipe through rail in **Public** mode; Email/Finance are completely absent from rail and voice command "open email" has no effect. Pass if private apps are invisible and unreachable.
- **AT‑03:** "Mira private mode <code> → open email → read that → back → public mode". Pass if mode gates behave and Email becomes accessible only in private mode.
- **AT‑04:** Enable debug overlay; verify landmarks, GN/IAN, dwell, timing panels visible.
- **AT‑05:** Power cycle; system wakes in **Public**; private persists only when explicitly set again.

---

## 10) Risks & Mitigations

- **Gesture misfires:** use confirmations for global/destructive; tune dwell/velocity; provide voice parity.
- **Landmark jitter:** steadyMs gating + hysteresis; per‑user calibration.
- **Privacy leaks:** hide sensitive apps entirely in Public; routing guard; no partial render of sensitive data.
- **Latency on Pi:** WS batching; reduce overlay FPS when enabled.

---

## 11) Backlog (Post‑MVP)

- Smart‑Home Lite, Now Playing, Workout Counter, Ambient Scenes.
- Per‑app quick‑actions palette.
- Multi‑user profiles & individual private codes.
- Rich Calendar (week view, RSVP) and live Commute.
- Sound cues “quiet hours”.

---

## 12) Owner Actions (You)

- Pick a **private mode code** (one word).
- Confirm **dwell ON by default** is acceptable (current: ON @ 700 ms).
- Confirm **focus ring** style preference: **High‑contrast pulse** vs **Subtle glow**.
- Confirm **voice**: default system TTS or a preferred voice.
- Provide Calendar source for MVP: **mock** or **local .ics**.

---

## 13) Running Summary (v1.0)

- **Hands‑free** via voice+gestures; **either‑hand** modifier for GN vs IAN.
- **Public Mode** hides Email/Finance entirely; **Settings fully visible in Public**; Private via code phrase.
- **Debug Overlay** is comprehensive and voice‑toggled.
- **MVP apps:** Home, Weather, Email, Finance, News, Todos, Calendar. **Commute** = reach goal.
- **Segmented build plan** from spec → reducer/router → shell/overlay → apps → privacy/calibration → device → reach goal.
