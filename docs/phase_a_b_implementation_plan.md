# Phase A & B Implementation Plan

**Date:** 2025-01-21  
**Purpose:** Detailed implementation plan mapping Phase A (Spec & Scaffolding) and Phase B (UI Shell & Debug) from `mira_mvp_ui_ux_plan.md` to existing codebase.

---

## Current State Analysis

### What Exists

#### Frontend (`frontend/`)

- ✅ Basic React + TypeScript + Vite setup
- ✅ App routing with `morning` and `ambient` modes
- ✅ WebSocket connections for vision and control plane state
- ✅ Components: `ModeSwitcher`, `SettingsPanel`, `VisionPanel`, `Toast`, `Quadrant`
- ✅ Features: Calendar, Weather, News, Todos, Vision panels
- ✅ State management: Local React state, WebSocket state patches
- ✅ Voice command interpretation via backend API
- ✅ Basic gesture detection display (VisionIntent)

#### Backend (`backend/`)

- ✅ FastAPI backend with authentication
- ✅ Voice interpretation endpoint (`/api/v1/voice/interpret`)
- ✅ REST APIs for todos, morning report, settings
- ✅ WebSocket endpoints for vision streaming

#### Control Plane (`control-plane/`)

- ✅ State management (`state.py`)
- ✅ Command arbiter (`arbiter.py`)
- ✅ State patches via WebSocket
- ✅ Command → Event → StatePatch pipeline
- ✅ SQLite persistence

#### Gesture Worker (`gesture-worker/`)

- ✅ MediaPipe hand detection
- ✅ Basic gesture classification (palm, fist, swipe left/right)
- ✅ Vision stream publishing to Redis
- ✅ Command sending to Control Plane
- ✅ Single-hand gesture detection

### What's Missing for Phase A & B

#### Phase A Requirements

1. ❌ Constants & env config (wake keyword, dwell, private code)
2. ❌ MediaPipe reducer with full gesture detection (pinch, two-finger, dwell)
3. ❌ Two-hand modifier detection (GN armed logic)
4. ❌ Command router merging gesture + voice
5. ❌ Public/Private mode with app filtering

#### Phase B Requirements

6. ❌ App Rail component (GN-only visibility)
7. ❌ HUD chips (mic, cam, WS, privacy, debug)
8. ❌ Focus ring + dwell visualizer
9. ❌ Debug overlay (camera + landmarks + diagnostics)

---

## Phase A: Spec & Scaffolding

### 1. Lock Constants & Environment Config

**Files to Create/Modify:**

- `frontend/src/lib/constants.ts` (NEW)
- `frontend/.env.example` (UPDATE)
- `backend/app/config.py` or `backend/app/core/constants.py` (NEW)
- `control-plane/app/core/constants.py` (NEW)
- `env.example` (UPDATE)

**Constants Needed:**

```typescript
// frontend/src/lib/constants.ts
export const WAKE_KEYWORD = 'mira'; // regex word boundary, case-insensitive
export const DWELL_MS_DEFAULT = 700; // tuneable, default ON
export const GN_STEADY_MS = 250; // steady open hand duration
export const GN_HYSTERESIS_MS = 120; // prevent flicker
export const PRIVACY_IDLE_TIMEOUT_MS = 300000; // 5 min
export const PRIVATE_CODE = process.env.VITE_PRIVATE_CODE || 'unlock'; // from env
```

**Environment Variables:**

- `VITE_WAKE_KEYWORD` (default: "mira")
- `VITE_DWELL_MS` (default: 700)
- `VITE_PRIVATE_CODE` (required)
- `VITE_GN_STEADY_MS` (default: 250)
- `VITE_GN_HYSTERESIS_MS` (default: 120)

**Decisions:**

- ✅ **Default private code**: Set backup in code as `'unlock'`, user will set `VITE_PRIVATE_CODE` in `.env` file
- ✅ **Constants**: Compile-time only (no runtime configuration)
- 📝 **TODO**: Remind user to set `VITE_PRIVATE_CODE` in `.env` after implementation

---

### 2. MediaPipe Reducer (Gesture Worker Enhancement)

**Current State:**

- `gesture-worker/src/gesture_worker_full.py` has basic gestures: palm, fist, swipe left/right
- Missing: pinch, two-finger, dwell detection
- Missing: velocity tracking, steadyMs tracking per hand

**Files to Modify:**

- `gesture-worker/src/gesture_worker_full.py`
- `control-plane/app/core/state.py` (add SensorsState)
- `frontend/src/lib/types.ts` (add SensorsState types)

**Required Enhancements:**

1. **Hand Tracking:**

   - Track both hands independently (MediaPipe supports up to 4 hands)
   - Compute velocity (x, y, magnitude) per hand
   - Track `steadyMs` (duration hand has been in current pose)
   - Store pose per hand: `"open" | "fist" | "pinch" | "twoFinger" | "unknown"`

2. **New Gestures:**

   - **Pinch**: Index finger and thumb tips close together (distance < threshold)
   - **Two-finger**: Index and middle finger extended, others closed
   - **Dwell**: Focus on element for ≥ 700ms (handled in frontend reducer)

3. **Data Structure:**

```python
# gesture-worker output should include:
{
  "hands": {
    "left": {
      "present": bool,
      "pose": "open" | "fist" | "pinch" | "twoFinger" | "unknown",
      "velocity": {"x": float, "y": float, "mag": float},
      "steadyMs": int
    },
    "right": { ... }
  },
  "gesture": "swipe_left" | "swipe_right" | "pinch" | "fist" | "twoFinger" | "idle",
  "confidence": float
}
```

**Decisions:**

- ✅ **Gesture worker output**: Only publish classified gestures (no raw hand data)
- 🔧 **Implementation**: Pinch/two-finger detection via finger tip distances (simpler, more reliable)
- 🔧 **Velocity threshold**: Use existing swipe detection logic, tune as needed during testing

---

### 3. Context Detector (GN Armed Logic)

**Current State:**

- Gesture worker has basic `armed` flag (palm detection)
- No two-hand modifier logic
- No hysteresis implementation

**Files to Create/Modify:**

- `gesture-worker/src/gesture_worker_full.py` (UPDATE) - Add GN armed computation
- `control-plane/app/core/state.py` (UPDATE) - Add `gnArmed` to state
- `control-plane/app/core/arbiter.py` (UPDATE) - Handle GN armed state patches
- `frontend/src/lib/types.ts` (UPDATE) - Add `gnArmed` to UIState type

**Logic (Python in Gesture Worker):**

```python
# GN armed computation in gesture worker
def compute_gn_armed(hands_data, prev_gn_armed, prev_time):
    """
    Compute GN armed state based on two-hand modifier model.
    Either hand can be the modifier (steady open hand).
    """
    now = time.time()
    steady_hand = find_steady_open_hand(hands_data, GN_STEADY_MS)
    other_hand = find_other_hand(hands_data, steady_hand)

    if steady_hand and other_hand and other_hand['pose'] != 'unknown':
        # Potential GN armed
        if not prev_gn_armed:
            # Apply hysteresis: require 250ms steady before arming
            if steady_hand['steadyMs'] >= GN_STEADY_MS:
                return True
        else:
            # Already armed - apply hysteresis to prevent flicker
            if steady_hand['steadyMs'] < GN_STEADY_MS - GN_HYSTERESIS_MS:
                return False
            return True

    # Disarm if no steady hand or both hands gesturing
    if prev_gn_armed:
        # Hysteresis: keep armed for 120ms after condition fails
        if (now - prev_time) * 1000 < GN_HYSTERESIS_MS:
            return True
    return False
```

**Decisions:**

- ✅ **GN armed computation**: In gesture worker (minimize frontend logic)
- ✅ **GN armed state tracking**: In Control Plane state
- ✅ **Edge cases**: Process and manage as needed (handle gracefully, don't ignore)

---

### 4. Command Router (Merge Gesture + Voice)

**Current State:**

- Voice commands go to backend → interpret → return intent
- Gesture commands go to Control Plane → arbiter → state patch
- No unified command router

**Files to Create/Modify:**

- `frontend/src/lib/commandRouter.ts` (NEW)
- `frontend/src/lib/gestureReducer.ts` (NEW)
- `control-plane/app/core/arbiter.py` (UPDATE) - Add new command types
- `frontend/src/lib/types.ts` (UPDATE) - Add command types

**Command Types:**

```typescript
type Command =
  // Global Navigation (GN)
  | { type: 'nav.nextApp' }
  | { type: 'nav.prevApp' }
  | { type: 'nav.openAppFocused' }
  | { type: 'nav.backOrHome' }

  // In-App Navigation (IAN)
  | { type: 'app.navigate'; payload: 'next' | 'prev' }
  | { type: 'app.selectFocus' }
  | { type: 'app.quickActions' }

  // Voice App Switching
  | { type: 'voice.openApp'; payload: { app: AppId } }
  | {
      type: 'voice.nav';
      payload: { action: 'next' | 'prev' | 'back' | 'select' };
    }

  // System
  | { type: 'system.toggleDebug' }
  | {
      type: 'system.setMode';
      payload: { mode: 'public' | 'private'; code?: string };
    };
```

**Router Logic:**

1. Receive gesture or voice intent
2. For gestures: Check GN armed state from Control Plane
3. Map to appropriate command type (GN vs IAN based on context)
4. For voice: Translate to GN or IAN commands as appropriate
5. Send to Control Plane arbiter
6. Handle confirmations for low-confidence destructive actions

**Decisions:**

- ✅ **Voice commands**: Handle both GN and regular nav by translating appropriately
  - App switching commands → GN commands
  - "next", "previous" → Context-aware (GN if appropriate, else IAN)
- 🔧 **Confirmations**: To be determined during implementation (likely mode switch, delete)
- 🔧 **Command conflicts**: Last command wins (voice takes precedence if simultaneous)

---

### 5. Public/Private Policy (Route Guard + App Registry)

**Current State:**

- No privacy mode implementation
- No app filtering

**Files to Create/Modify:**

- `frontend/src/lib/appRegistry.ts` (NEW)
- `frontend/src/lib/privacyPolicy.ts` (NEW)
- `frontend/src/App.tsx` (UPDATE) - Add privacy mode state
- `control-plane/app/core/state.py` (UPDATE) - Add `ui.mode` to state
- `frontend/src/lib/types.ts` (UPDATE) - Add UIState type

**App Registry:**

```typescript
const APP_REGISTRY: AppId[] = [
  'home',
  'weather',
  'email', // Private only
  'finance', // Private only
  'news',
  'todos',
  'calendar',
  'settings', // Always visible
];

function getVisibleApps(mode: 'public' | 'private'): AppId[] {
  if (mode === 'public') {
    return APP_REGISTRY.filter((id) => id !== 'email' && id !== 'finance');
  }
  return APP_REGISTRY;
}
```

**Route Guard:**

- Filter app routes based on mode
- Block voice commands for hidden apps
- Filter app rail rendering

**Decisions:**

- ✅ **Private mode**: Requires code every time (no session memory)
- ✅ **Settings**: Fully visible in Public mode (per plan)
- ✅ **Mode switch behavior**: If switching from private to public while in a private app (email/finance), navigate back to home

---

## Phase B: UI Shell & Debug

### 6. App Rail (GN-Only Visibility)

**Current State:**

- No app rail component
- Mode switcher exists but not the same concept

**Files to Create:**

- `frontend/src/components/AppRail.tsx` (NEW)
- `frontend/src/components/AppRail.css` (NEW)

**Requirements:**

- Only visible when `gnArmed === true`
- Horizontal rail with app icons/names
- Order: `[Home, Weather, Email, Finance, News, Todos, Calendar, Settings]`
- Filtered by privacy mode (hide Email/Finance in Public)
- Focus indicator (highlight current app)
- Support swipe gestures to navigate

**Design:**

- Position: Top or bottom of screen
- Style: Horizontal row of icons with labels
- Animation: Slide in/out based on `gnArmed`
- Focus: Highlight current `appRoute`

**Questions:**

- [ ] Should rail be top or bottom? (Plan doesn't specify)
- [ ] Should rail show icons only or icons + labels?
- [ ] How should rail handle focus navigation (voice vs gesture)?

---

### 7. Focus Ring + Dwell Visualizer

**Current State:**

- No focus system
- No dwell detection

**Files to Create:**

- `frontend/src/components/FocusRing.tsx` (NEW)
- `frontend/src/lib/focusManager.ts` (NEW)
- `frontend/src/lib/dwellTracker.ts` (NEW)

**Requirements:**

1. **Focus Ring:**

   - High-contrast ring around focused element
   - Subtle pulse animation
   - Dwell-fill ring (fills over 700ms)

2. **Focus Path:**

   - Track `focusPath: string[]` in state (e.g., `['todos', '0']` for first todo)
   - Each app defines focusable elements

3. **Dwell Tracker:**
   - Track time focused on element
   - When ≥ 700ms, trigger `app.selectFocus`
   - Visual progress indicator

**Decisions:**

- ✅ **Focus ring style**: High-contrast pulse
- 🔧 **Focus in Home dashboard**: Hierarchical (panel → item within panel)
  - First focus level: panels (Calendar, Weather, News, Todos)
  - Second focus level: items within panel (e.g., individual todos)

---

### 8. HUD Chips

**Current State:**

- Settings panel shows some status info
- No persistent HUD

**Files to Create:**

- `frontend/src/components/HUD.tsx` (NEW)
- `frontend/src/components/HUD.css` (NEW)

**Chips Needed:**

- **Mic**: `hud.micOn` (from state)
- **Cam**: `hud.camOn` (from state)
- **WS**: `hud.wsConnected` (from state)
- **Privacy**: Public (hollow icon) vs Private (solid lock) with color tint
- **Debug**: `debug.enabled` (from state)
- **Wake**: `hud.wake` (indicates wake phrase detected)

**Design:**

- Position: Corner of screen (top-right suggested)
- Style: Small chips with icons
- Color coding: Green (on/connected), Red (off/disconnected), Amber (private)

**Questions:**

- [ ] Which corner for HUD? (top-right suggested)
- [ ] Should HUD always be visible or only in certain modes?

---

### 9. Debug Overlay

**Current State:**

- VisionPanel shows camera preview but not full debug overlay
- No landmarks overlay
- No gesture/ASR diagnostics
- No timing panels

**Files to Create/Modify:**

- `frontend/src/components/DebugOverlay.tsx` (NEW)
- `frontend/src/components/DebugOverlay.css` (NEW)
- `frontend/src/App.tsx` (UPDATE) - Toggle debug overlay
- `backend/app/api/vision.py` or gesture worker (UPDATE) - Send landmarks data

**Requirements:**

1. **Camera Preview:**

   - Live camera feed with MediaPipe hand landmarks overlaid
   - Pose labels (open, fist, pinch, etc.)
   - FPS counter

2. **Gesture Stream:**

   - Last N frames of gesture data
   - Pose, velocity, confidence per hand
   - GN/IAN state

3. **Mode/State Panel:**

   - Current `appRoute`
   - Current `focusPath`
   - `ui.mode` (public/private)
   - `gnArmed` status

4. **Timing Panel:**

   - Gesture → intent ms
   - Intent → statePatch ms
   - WebSocket latency
   - FPS

5. **Voice Panel:**

   - Wake phrase hits
   - Last ASR transcript
   - Last intent + confidence

6. **Dwell Visualizer:**

   - Show current focus target
   - Progress bar for dwell time

7. **Privacy Banner:**
   - Current mode's policy
   - Visible apps list

**Activation:**

- Voice command: "Mira enable debug overlay" / "Mira disable debug"
- Toggle via HUD chip (if enabled)

**Questions:**

- [ ] Should landmarks be rendered in frontend or sent from gesture worker?
- [ ] How many frames of gesture history should we show?
- [ ] Should debug overlay be fullscreen or overlay panel?

---

## Data Flow Architecture

### Current Flow:

```
Gesture Worker → Redis → Backend WS → Frontend (VisionIntent)
Voice → Backend API → Frontend (VoiceInterpretResponse)
Control Plane → State Patches → Frontend
```

### Target Flow (Phase A):

```
Gesture Worker (GN armed + gestures) → Control Plane → State Patches → Frontend
Voice → Backend API → Control Plane → State Patches → Frontend
Control Plane → State Patches → Frontend (UIState)
```

### Key Changes:

1. **Gesture Worker Enhancement**: Computes GN armed state, publishes classified gestures with GN context
2. **Command Router**: In Control Plane arbiter - unified entry point for gesture + voice commands
3. **State Management**: UIState in Control Plane, synced via WebSocket to frontend
4. **Privacy Filtering**: Frontend filters apps based on mode from Control Plane state
5. **Minimal Frontend Logic**: All computation in gesture worker or control plane

---

## Implementation Order

### Phase A Tasks:

1. ✅ Create constants & env config (compile-time only)
2. ✅ Enhance gesture worker:
   - Add pinch, two-finger detection
   - Track velocity, steadyMs per hand
   - Compute GN armed state (two-hand modifier)
   - Publish classified gestures with GN context
3. ✅ Update Control Plane state to include UIState (mode, appRoute, focusPath, gnArmed, debug, hud)
4. ✅ Update Control Plane arbiter with command router logic
5. ✅ Implement app registry & privacy policy (frontend)
6. ✅ Update voice intents to support new commands (translate GN/IAN)
7. ✅ Handle mode switching (private → public navigates to home if in private app)

### Phase B Tasks:

9. ✅ Create App Rail component
10. ✅ Create HUD component
11. ✅ Create Focus Ring component
12. ✅ Create Dwell Tracker
13. ✅ Create Debug Overlay component
14. ✅ Integrate all components into App.tsx
15. ✅ Add voice commands for debug toggle

---

## Architecture Decisions Summary

### ✅ Resolved Decisions

1. **Private Code**: Default `'unlock'` in code, user sets `VITE_PRIVATE_CODE` in `.env`
2. **Focus Ring Style**: High-contrast pulse
3. **Constants**: Compile-time only
4. **Gesture Worker Output**: Only classified gestures (no raw hand data)
5. **GN Armed Computation**: In gesture worker (minimize frontend logic)
6. **GN Armed State**: Tracked in Control Plane
7. **Voice Commands**: Handle both GN and IAN by translating appropriately
8. **Private Mode**: Requires code every time
9. **Mode Switch**: Navigate to home when switching from private to public while in private app
10. **Edge Cases**: Process and manage as needed

### 🔧 Remaining Questions (Can be decided during implementation)

1. **App Rail Position**: Top or bottom of screen? (Recommend: top)
2. **HUD Position**: Which corner? (Recommend: top-right)
3. **Dwell Default**: 700ms acceptable? (Recommend: yes, matches plan)
4. **Voice TTS**: Default system TTS or preferred voice? (Recommend: default system for MVP)
5. **Calendar Source**: Mock data or local .ics file? (Recommend: mock for MVP)
6. **Debug Overlay**: Fullscreen or overlay panel? (Recommend: overlay panel)
7. **Landmarks Rendering**: Frontend or backend? (Recommend: backend sends landmarks, frontend renders)
8. **Confirmations**: Which commands need confirmations? (Recommend: mode switch, delete actions)

---

## Testing Strategy

### Unit Tests:

- Context detector logic (GN armed computation)
- Command router (gesture → command mapping)
- Privacy policy (app filtering)
- Focus manager (focus path navigation)

### Integration Tests:

- Gesture → Command → State Patch flow
- Voice → Command → State Patch flow
- Privacy mode filtering (app rail, routing)
- Debug overlay toggle

### Manual Acceptance Tests:

- AT-01: Voice navigation through apps
- AT-02: GN swipe in Public mode (Email/Finance hidden)
- AT-03: Private mode with code
- AT-04: Debug overlay visibility
- AT-05: Power cycle → Public mode default

---

## Next Steps

1. ✅ **Plan reviewed** and decisions documented
2. ✅ **Architecture clarified**: Computation in gesture worker/control plane, minimal frontend logic
3. **Ready for implementation** (Phase A first, then Phase B)
4. **Post-implementation**: Remind user to set `VITE_PRIVATE_CODE` in `.env` file

---

## Implementation Notes

### 📝 Post-Implementation Reminders

After Phase A & B are complete, remind user to:

- Set `VITE_PRIVATE_CODE` environment variable in `.env` file (currently defaults to `'unlock'` in code)

### 🏗️ Architecture Principles

1. **Minimize Frontend Logic**: All computation happens in gesture worker or control plane
2. **State Management**: UIState lives in Control Plane, synced via WebSocket
3. **Gesture Processing**: Only classified gestures published (no raw hand data)
4. **Privacy First**: Private mode requires code every time, no session memory
