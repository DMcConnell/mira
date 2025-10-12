"""
Production Gesture Worker
Captures video, detects hand gestures, and emits both:
1. Raw gesture data to Redis (for /ws/vision streaming)
2. Debounced commands to Control Plane (for state changes)
"""

import asyncio
import json
import os
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Deque, Optional, Tuple

import cv2
import httpx
import mediapipe as mp
import numpy as np
import redis.asyncio as aioredis

# Environment configuration
ENV = os.getenv("MIRA_ENV", "mac")  # "mac" or "pi"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CONTROL_PLANE_URL = os.getenv("CONTROL_PLANE_URL", "http://localhost:8090")
VISION_CHANNEL = "mira:vision"  # Redis channel for raw vision data

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
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        return cap


class GestureWorker:
    """
    Gesture detection worker that:
    1. Captures video frames
    2. Runs MediaPipe hand detection
    3. Classifies static (palm, fist, point) and dynamic (swipe) gestures
    4. Publishes raw data to Redis for UI streaming
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
            max_num_hands=2,
            min_detection_confidence=0.4,
            min_tracking_confidence=0.4,
        )

        # Gesture tracking
        self.centroid_buffer: Deque[Tuple[float, float]] = deque(maxlen=16)
        self.last_gesture = "idle"
        self.last_command_time = 0
        self.cooldown_duration = 0.5  # seconds between commands
        self.armed = False

        # Redis client (will be initialized async)
        self.redis: Optional[aioredis.Redis] = None

        # HTTP client for Control Plane
        self.http_client: Optional[httpx.AsyncClient] = None

    def compute_centroid_x(self, landmarks) -> float:
        """Compute normalized x-coordinate of hand centroid"""
        xs = [lm.x for lm in landmarks.landmark]
        return float(np.mean(xs))

    def classify_static_gesture(self, landmarks) -> str:
        """
        Classify static hand gestures based on finger extension.
        Returns: 'palm', 'fist', 'point', or 'idle'
        """
        # Get landmark positions (normalized 0-1)
        # Index finger
        idx_tip_y = landmarks.landmark[8].y
        idx_pip_y = landmarks.landmark[6].y

        # Middle finger
        mid_tip_y = landmarks.landmark[12].y
        mid_pip_y = landmarks.landmark[10].y

        # Ring finger
        ring_tip_y = landmarks.landmark[16].y
        ring_pip_y = landmarks.landmark[14].y

        # Pinky finger
        pinky_tip_y = landmarks.landmark[20].y
        pinky_pip_y = landmarks.landmark[18].y

        # Thumb (different check - compare tip to MCP)
        thumb_tip_x = landmarks.landmark[4].x
        thumb_mcp_x = landmarks.landmark[2].x
        thumb_extended = abs(thumb_tip_x - thumb_mcp_x) > 0.1

        # Check if fingers are extended (tip above pip in image coords)
        fingers_extended = [
            idx_tip_y < idx_pip_y,
            mid_tip_y < mid_pip_y,
            ring_tip_y < ring_pip_y,
            pinky_tip_y < pinky_pip_y,
        ]

        # Classify
        if all(fingers_extended) and thumb_extended:
            return "palm"
        elif not any(fingers_extended) and not thumb_extended:
            return "fist"
        elif fingers_extended[0] and not any(fingers_extended[1:]):
            return "point"
        else:
            return "idle"

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

        # Thresholds (tunable) - made more forgiving for testing
        MIN_DISPLACEMENT = 0.15  # 15% of screen width (reduced from 20%)
        MIN_DURATION = 0.50  # at least 100ms (reduced from 150ms)
        MAX_DURATION = 2.00  # no more than 600ms (increased from 500ms)

        # Debug output every 10 frames when buffer is full
        if len(self.centroid_buffer) >= 10 and int(current_time * 10) % 10 == 0:
            print(
                f"  Buffer: {len(self.centroid_buffer)} frames, dx={dx:.3f}, duration={duration:.3f}s"
            )

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

    async def publish_vision_intent(self, gesture: str, confidence: float):
        """Publish raw gesture data to Redis for real-time streaming"""
        if not self.redis:
            return

        intent = {
            "tsISO": datetime.now(timezone.utc).isoformat(),
            "gesture": gesture,
            "confidence": confidence,
            "armed": self.armed,
        }

        try:
            await self.redis.publish(VISION_CHANNEL, json.dumps(intent))
        except Exception as e:
            print(f"Error publishing vision intent: {e}")

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
        hand_detected = False

        if results.multi_hand_landmarks:
            hand_detected = True
            # Use first detected hand
            hand_landmarks = results.multi_hand_landmarks[0]

            # Classify static gesture
            static_gesture = self.classify_static_gesture(hand_landmarks)
            gesture = static_gesture
            confidence = 0.85 if gesture != "idle" else 0.95

            # Update armed state (palm gesture arms the system)
            if gesture == "palm":
                self.armed = True
            elif gesture == "idle":
                self.armed = False

            # Track centroid for swipe detection
            cx = self.compute_centroid_x(hand_landmarks)
            self.centroid_buffer.append((current_time, cx))

            # Detect dynamic gestures (swipes) - always check, not just when armed
            swipe = self.detect_swipe(current_time)
            if swipe:
                gesture = swipe
                confidence = 0.90
                print(
                    f"SWIPE DETECTED: {swipe} (buffer size: {len(self.centroid_buffer)})"
                )

            # Draw landmarks on frame (for debugging/preview)
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # Always publish raw vision data for streaming
        await self.publish_vision_intent(gesture, confidence)

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
            }
            await self.send_command(action, payload)
            self.last_command_time = current_time

        self.last_gesture = gesture

        return frame, gesture, confidence

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
                frame, gesture, confidence = await self.process_frame(
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
                # Show buffer size and armed state
                cv2.putText(
                    frame,
                    f"Buffer: {len(self.centroid_buffer)}/16 | Armed: {self.armed}",
                    (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 255) if self.armed else (100, 100, 100),
                    1,
                )

                # Show frame (disable in production/headless mode)
                if ENV == "mac":
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
