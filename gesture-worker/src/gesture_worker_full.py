"""
Production Gesture Worker - Enhanced for Phase A
Captures video, detects hand gestures, and emits both:
1. Classified gesture data to Redis (for /ws/vision streaming)
2. Debounced commands to Control Plane (for state changes)

Supports:
- Multiple hands (left/right)
- Pinch, two-finger gestures
- Velocity and steadyMs tracking per hand
- GN armed computation (two-hand modifier model)
"""

import asyncio
import base64
import json
import os
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Dict, Optional, Tuple

import cv2
import httpx
import mediapipe as mp
import numpy as np
import redis.asyncio as aioredis

# Constants from plan
GN_STEADY_MS = 250  # steady open hand duration for GN armed
GN_HYSTERESIS_MS = 120  # prevent flicker in GN armed state
PINCH_THRESHOLD = 0.05  # normalized distance threshold for pinch detection

# Environment configuration
ENV = os.getenv("MIRA_ENV", "mac")  # "mac" or "pi"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CONTROL_PLANE_URL = os.getenv("CONTROL_PLANE_URL", "http://localhost:8090")
SHOW_PREVIEW_WINDOW = os.getenv("SHOW_PREVIEW_WINDOW", "false").lower() == "true"
VISION_CHANNEL = "mira:vision"  # Redis channel for raw vision data
SNAPSHOT_KEY = "mira:vision:snapshot"  # Redis key for latest frame snapshot

# MediaPipe setup
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


def open_capture(width=640, height=360, fps=30):
    """Open camera based on environment (Mac or Pi)"""
    if ENV == "pi":
        try:
            # Picamera2 path (preferred on Pi)
            from picamera2 import Picamera2

            picam = Picamera2()
            config = picam.create_preview_configuration(
                main={"size": (width, height), "format": "RGB888"}
            )
            picam.configure(config)
            picam.start()

            class PiCap:
                def read(self):
                    frame = picam.capture_array()
                    return True, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                def release(self):
                    picam.stop()

                def isOpened(self):
                    return True

            return PiCap()
        except Exception as e:
            print(f"Failed to use Picamera2, falling back to GStreamer: {e}")
            # Fallback: GStreamer → OpenCV
            pipeline = (
                "libcamerasrc ! video/x-raw, width=%d, height=%d, framerate=%d/1 ! "
                "videoconvert ! video/x-raw,format=BGR ! appsink" % (width, height, fps)
            )
            cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            return cap
    else:
        # macOS (and generic USB cams)
        cap = cv2.VideoCapture(1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        return cap


class HandTracker:
    """Tracks individual hand state: pose, velocity, steadyMs"""

    def __init__(self):
        self.pose = "unknown"
        self.pose_start_time = 0.0
        self.last_centroid = (0.0, 0.0)
        self.velocity_history: Deque[Tuple[float, float, float]] = deque(
            maxlen=5
        )  # (time, x, y)

    def update_pose(self, new_pose: str, current_time: float):
        """Update pose and track steady time"""
        if new_pose != self.pose:
            self.pose = new_pose
            self.pose_start_time = current_time

    def get_steady_ms(self, current_time: float) -> int:
        """Get how long the hand has been in current pose (ms)"""
        if self.pose_start_time == 0:
            return 0
        return int((current_time - self.pose_start_time) * 1000)

    def update_velocity(self, centroid: Tuple[float, float], current_time: float):
        """Update velocity based on centroid movement"""
        if self.last_centroid == (0.0, 0.0):
            self.last_centroid = centroid
            return

        dt = current_time - (
            self.velocity_history[-1][0] if self.velocity_history else current_time
        )
        if dt > 0:
            dx = centroid[0] - self.last_centroid[0]
            dy = centroid[1] - self.last_centroid[1]
            vx = dx / dt if dt > 0 else 0.0
            vy = dy / dt if dt > 0 else 0.0
            mag = np.sqrt(vx * vx + vy * vy)

            self.velocity_history.append((current_time, vx, vy))
            self.last_centroid = centroid

    def get_velocity(self) -> Dict[str, float]:
        """Get current velocity (x, y, magnitude)"""
        if not self.velocity_history:
            return {"x": 0.0, "y": 0.0, "mag": 0.0}

        # Use most recent velocity
        _, vx, vy = self.velocity_history[-1]
        mag = np.sqrt(vx * vx + vy * vy)
        return {"x": float(vx), "y": float(vy), "mag": float(mag)}


class GestureWorker:
    """
    Enhanced gesture detection worker that:
    1. Tracks multiple hands independently
    2. Detects pinch, two-finger gestures
    3. Computes GN armed state (two-hand modifier)
    4. Publishes classified gestures to Redis
    5. Sends debounced commands to Control Plane
    """

    def __init__(
        self,
        width: int = 640,
        height: int = 360,
        fps: int = 30,
    ):
        self.width = width
        self.height = height
        self.fps = fps

        # Video capture
        self.cap = open_capture(width, height, fps)
        if not self.cap.isOpened():
            raise RuntimeError("Failed to open camera")

        # MediaPipe Hands
        self.hands = mp_hands.Hands(
            model_complexity=0,
            max_num_hands=4,
            min_detection_confidence=0.4,
            min_tracking_confidence=0.4,
        )

        # Hand tracking (by MediaPipe hand ID)
        self.hand_trackers: Dict[int, HandTracker] = {}

        # Gesture tracking
        self.centroid_buffer: Deque[Tuple[float, float]] = deque(maxlen=16)
        self.last_gesture = "idle"
        self.last_command_time = 0
        self.cooldown_duration = 0.5  # seconds between commands

        # GN armed state tracking
        self.gn_armed = False
        self.prev_gn_armed = False
        self.prev_gn_time = 0.0

        # Redis client (will be initialized async)
        self.redis: Optional[aioredis.Redis] = None

        # HTTP client for Control Plane
        self.http_client: Optional[httpx.AsyncClient] = None

        # Frame snapshot publishing (throttled to ~10 FPS)
        self.last_snapshot_time = 0.0
        self.snapshot_interval = 0.1  # ~10 FPS

    def compute_centroid(self, landmarks) -> Tuple[float, float]:
        """Compute normalized (x, y) centroid of hand"""
        xs = [lm.x for lm in landmarks.landmark]
        ys = [lm.y for lm in landmarks.landmark]
        return float(np.mean(xs)), float(np.mean(ys))

    def compute_distance(self, p1, p2) -> float:
        """Compute normalized distance between two points"""
        dx = p1.x - p2.x
        dy = p1.y - p2.y
        return np.sqrt(dx * dx + dy * dy)

    def classify_static_gesture(self, landmarks) -> str:
        """
        Classify static hand gestures based on finger extension.
        Returns: 'open', 'fist', 'pinch', 'twoFinger', or 'unknown'
        """
        # Get landmark positions (normalized 0-1)
        # Index finger
        idx_tip = landmarks.landmark[8]
        idx_pip = landmarks.landmark[6]
        idx_mcp = landmarks.landmark[5]

        # Middle finger
        mid_tip = landmarks.landmark[12]
        mid_pip = landmarks.landmark[10]
        mid_mcp = landmarks.landmark[9]

        # Ring finger
        ring_tip = landmarks.landmark[16]
        ring_pip = landmarks.landmark[14]

        # Pinky finger
        pinky_tip = landmarks.landmark[20]
        pinky_pip = landmarks.landmark[18]

        # Thumb
        thumb_tip = landmarks.landmark[4]
        thumb_ip = landmarks.landmark[3]

        # Check if fingers are extended (tip above pip in image coords)
        idx_extended = idx_tip.y < idx_pip.y
        mid_extended = mid_tip.y < mid_pip.y
        ring_extended = ring_tip.y < ring_pip.y
        pinky_extended = pinky_tip.y < pinky_pip.y
        thumb_extended = abs(thumb_tip.x - thumb_ip.x) > 0.1

        fingers_extended = [
            idx_extended,
            mid_extended,
            ring_extended,
            pinky_extended,
        ]

        # Check for pinch (thumb and index tip close together)
        pinch_distance = self.compute_distance(thumb_tip, idx_tip)
        is_pinch = pinch_distance < PINCH_THRESHOLD

        # Check for two-finger (index and middle extended, others closed)
        is_two_finger = idx_extended and mid_extended and not any(fingers_extended[2:])

        # Classify
        if is_pinch and not idx_extended:
            return "pinch"
        elif is_two_finger:
            return "twoFinger"
        elif all(fingers_extended) and thumb_extended:
            return "open"
        elif not any(fingers_extended) and not thumb_extended:
            return "fist"
        else:
            return "unknown"

    def detect_swipe(self, current_time: float) -> Optional[str]:
        """
        Detect horizontal swipe gestures from centroid buffer.
        Returns: 'swipe_left', 'swipe_right', or None
        """
        if len(self.centroid_buffer) < 8:
            return None

        t0, x0 = self.centroid_buffer[0]
        t1, x1 = self.centroid_buffer[-1]

        dx = x1 - x0
        duration = t1 - t0

        # Thresholds
        MIN_DISPLACEMENT = 0.15  # 15% of screen width
        MIN_DURATION = 0.50  # at least 500ms
        MAX_DURATION = 2.00  # no more than 2s

        if (
            duration > MIN_DURATION
            and duration < MAX_DURATION
            and abs(dx) > MIN_DISPLACEMENT
        ):
            if dx > 0:
                return "swipe_right"
            else:
                return "swipe_left"

        return None

    def compute_gn_armed(
        self, hands_data: Dict[str, Dict], current_time: float
    ) -> bool:
        """
        Compute GN armed state based on two-hand modifier model.
        Either hand can be the modifier (steady open hand).
        """
        # Find steady open hand (≥ 250ms)
        steady_hand = None
        other_hand = None

        for hand_id, hand_data in hands_data.items():
            if hand_data["pose"] == "open" and hand_data["steadyMs"] >= GN_STEADY_MS:
                steady_hand = hand_id
                break

        # Find other hand (not the steady one, and performing a gesture)
        for hand_id, hand_data in hands_data.items():
            if hand_id != steady_hand and hand_data["pose"] != "unknown":
                other_hand = hand_id
                break

        if steady_hand and other_hand:
            # Potential GN armed
            if not self.prev_gn_armed:
                # Apply hysteresis: require 250ms steady before arming
                if hands_data[steady_hand]["steadyMs"] >= GN_STEADY_MS:
                    return True
            else:
                # Already armed - apply hysteresis to prevent flicker
                if hands_data[steady_hand]["steadyMs"] < (
                    GN_STEADY_MS - GN_HYSTERESIS_MS
                ):
                    return False
                return True

        # Disarm if no steady hand or both hands gesturing
        if self.prev_gn_armed:
            # Hysteresis: keep armed for 120ms after condition fails
            if (current_time - self.prev_gn_time) * 1000 < GN_HYSTERESIS_MS:
                return True

        return False

    def encode_frame_as_jpeg(self, frame) -> Optional[str]:
        """Encode frame as base64-encoded JPEG"""
        try:
            # Encode frame as JPEG (quality 80 for faster encoding while maintaining visual quality)
            success, encoded = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
            )
            if not success:
                return None
            # Convert to base64
            jpeg_bytes = encoded.tobytes()
            base64_str = base64.b64encode(jpeg_bytes).decode("utf-8")
            return base64_str
        except Exception as e:
            print(f"Error encoding frame: {e}")
            return None

    async def publish_frame_snapshot(self, frame, current_time: float):
        """Publish annotated frame as base64 JPEG to Redis (throttled)"""
        if not self.redis:
            return

        # Throttle to ~10 FPS
        if current_time - self.last_snapshot_time < self.snapshot_interval:
            return

        base64_jpeg = self.encode_frame_as_jpeg(frame)
        if not base64_jpeg:
            return

        try:
            # Store in Redis with 2 second TTL (will be refreshed if worker is alive)
            await self.redis.set(SNAPSHOT_KEY, base64_jpeg, ex=2)
            self.last_snapshot_time = current_time
        except Exception as e:
            print(f"Error publishing frame snapshot: {e}")

    async def publish_vision_intent(
        self, gesture: str, confidence: float, gn_armed: bool
    ):
        """Publish classified gesture data to Redis for real-time streaming"""
        if not self.redis:
            return

        intent = {
            "tsISO": datetime.now(timezone.utc).isoformat(),
            "gesture": gesture,
            "confidence": confidence,
            "armed": gn_armed,  # Keep for backward compatibility
            "gnArmed": gn_armed,  # New field
        }

        try:
            await self.redis.publish(VISION_CHANNEL, json.dumps(intent))
        except Exception as e:
            print(f"Error publishing vision intent: {e}")

    async def send_gn_armed_state(self, gn_armed: bool):
        """Send GN armed state to Control Plane"""
        if not self.http_client:
            return

        command = {
            "id": str(uuid.uuid4()),
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": "gesture",
            "action": "set_gn_armed",
            "payload": {"gnArmed": gn_armed},
        }

        try:
            response = await self.http_client.post(
                f"{CONTROL_PLANE_URL}/command",
                json=command,
                timeout=2.0,
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Error sending GN armed state: {e}")

    async def send_command(self, action: str, payload: dict):
        """Send debounced command to Control Plane"""
        if not self.http_client:
            return

        command = {
            "id": str(uuid.uuid4()),
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": "gesture",
            "action": action,
            "payload": payload,
        }

        try:
            response = await self.http_client.post(
                f"{CONTROL_PLANE_URL}/command",
                json=command,
                timeout=2.0,
            )
            response.raise_for_status()
            print(f"✓ Command sent: {action}")
        except Exception as e:
            print(f"Error sending command: {e}")

    async def process_frame(self, frame, current_time: float):
        """Process a single frame and emit gestures/commands"""
        # Convert to RGB for MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb)

        gesture = "idle"
        confidence = 0.0
        hands_data = {}

        if results.multi_hand_landmarks:
            # Process all detected hands
            for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                hand_label = (
                    results.multi_handedness[hand_idx].classification[0].label
                )  # "Left" or "Right"
                hand_id = hand_label.lower()

                # Initialize tracker if needed
                if hand_id not in self.hand_trackers:
                    self.hand_trackers[hand_id] = HandTracker()

                tracker = self.hand_trackers[hand_id]

                # Classify static gesture
                static_gesture = self.classify_static_gesture(hand_landmarks)
                tracker.update_pose(static_gesture, current_time)

                # Compute centroid and velocity
                centroid = self.compute_centroid(hand_landmarks)
                tracker.update_velocity(centroid, current_time)

                # Get hand state
                steady_ms = tracker.get_steady_ms(current_time)
                velocity = tracker.get_velocity()

                hands_data[hand_id] = {
                    "present": True,
                    "pose": static_gesture,
                    "steadyMs": steady_ms,
                    "velocity": velocity,
                }

                # Track centroid for swipe detection (use first hand)
                if hand_idx == 0:
                    cx, _ = centroid
                    self.centroid_buffer.append((current_time, cx))

                # Draw landmarks on frame (for debugging/preview)
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Determine primary gesture (use first hand for now)
            if hands_data:
                first_hand = list(hands_data.values())[0]
                gesture = first_hand["pose"]
                confidence = 0.85 if gesture != "idle" else 0.95

            # Detect dynamic gestures (swipes) - always check
            swipe = self.detect_swipe(current_time)
            if swipe:
                gesture = swipe
                confidence = 0.90

        # Mark missing hands as not present
        for hand_id in list(self.hand_trackers.keys()):
            if hand_id not in hands_data:
                hands_data[hand_id] = {
                    "present": False,
                    "pose": "unknown",
                    "steadyMs": 0,
                    "velocity": {"x": 0.0, "y": 0.0, "mag": 0.0},
                }

        # Compute GN armed state
        self.gn_armed = self.compute_gn_armed(hands_data, current_time)

        # Send GN armed state if it changed
        if self.gn_armed != self.prev_gn_armed:
            await self.send_gn_armed_state(self.gn_armed)
            self.prev_gn_armed = self.gn_armed
            self.prev_gn_time = current_time

        # Always publish classified gesture data for streaming
        await self.publish_vision_intent(gesture, confidence, self.gn_armed)

        # Send command if gesture changed and cooldown expired
        time_since_last_command = current_time - self.last_command_time
        if (
            gesture != self.last_gesture
            and gesture != "idle"
            and time_since_last_command > self.cooldown_duration
        ):
            action = f"gesture_{gesture}"
            payload = {
                "gesture": gesture,
                "confidence": confidence,
                "gnArmed": self.gn_armed,
            }
            await self.send_command(action, payload)
            self.last_command_time = current_time

        self.last_gesture = gesture

        return frame, gesture, confidence, self.gn_armed

    async def run(self):
        """Main worker loop"""
        print(f"🚀 Gesture Worker starting (ENV={ENV})...")
        print(f"   Camera: {self.width}x{self.height}@{self.fps}fps")
        print(f"   Redis: {REDIS_URL}")
        print(f"   Control Plane: {CONTROL_PLANE_URL}")

        # Initialize async clients
        self.redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        self.http_client = httpx.AsyncClient()

        print("✅ Connected to Redis and Control Plane")

        frame_count = 0
        fps_start = time.time()
        fps_display = 0

        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to read frame, retrying...")
                    await asyncio.sleep(0.1)
                    continue

                current_time = time.time()

                # Process frame
                frame, gesture, confidence, gn_armed = await self.process_frame(
                    frame, current_time
                )

                # Update FPS display
                frame_count += 1
                if frame_count % 30 == 0:
                    fps_display = 30 / (time.time() - fps_start)
                    fps_start = time.time()

                # Draw HUD
                cv2.putText(
                    frame,
                    f"FPS: {fps_display:.1f}",
                    (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )
                cv2.putText(
                    frame,
                    f"Gesture: {gesture} ({confidence:.2f})",
                    (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )
                cv2.putText(
                    frame,
                    f"GN Armed: {gn_armed}",
                    (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0) if gn_armed else (100, 100, 100),
                    2,
                )

                # Publish frame snapshot to Redis (throttled to ~10 FPS)
                await self.publish_frame_snapshot(frame, current_time)

                # Show frame window (optional, disabled by default - use browser preview instead)
                if SHOW_PREVIEW_WINDOW:
                    cv2.imshow("Gesture Worker", frame)
                    if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
                        break

                # Yield control to allow other async tasks
                await asyncio.sleep(0.001)

        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        finally:
            self.cap.release()
            cv2.destroyAllWindows()
            if self.redis:
                await self.redis.close()
            if self.http_client:
                await self.http_client.aclose()
            print("✅ Cleanup complete")


if __name__ == "__main__":
    worker = GestureWorker()
    asyncio.run(worker.run())
