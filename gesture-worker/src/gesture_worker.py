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
import time
from collections import deque
from typing import Deque, Dict, Tuple

import cv2
import mediapipe as mp

from .camera import open_capture
from .config import (
    COMMAND_COOLDOWN_DURATION,
    CONTROL_PLANE_URL,
    DEFAULT_FPS,
    DEFAULT_HEIGHT,
    DEFAULT_WIDTH,
    ENV,
    MEDIAPIPE_MAX_NUM_HANDS,
    MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
    MEDIAPIPE_MIN_TRACKING_CONFIDENCE,
    MEDIAPIPE_MODEL_COMPLEXITY,
    REDIS_URL,
    SHOW_PREVIEW_WINDOW,
    GN_STEADY_MS,
)
from .gesture_classifier import (
    classify_static_gesture,
    compute_centroid,
    compute_gn_armed,
    detect_swipe,
)
from .hand_tracker import HandTracker
from .logger import get_logger
from .publisher import Publisher

# MediaPipe setup
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# Logger
logger = get_logger(__name__)


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
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        fps: int = DEFAULT_FPS,
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
            model_complexity=MEDIAPIPE_MODEL_COMPLEXITY,
            max_num_hands=MEDIAPIPE_MAX_NUM_HANDS,
            min_detection_confidence=MEDIAPIPE_MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MEDIAPIPE_MIN_TRACKING_CONFIDENCE,
        )

        # Hand tracking (by MediaPipe hand ID)
        self.hand_trackers: Dict[str, HandTracker] = {}

        # Gesture tracking
        self.centroid_buffer: Deque[Tuple[float, float]] = deque(maxlen=16)
        self.last_gesture = "idle"
        self.last_command_time = 0
        self.cooldown_duration = COMMAND_COOLDOWN_DURATION

        # GN armed state tracking
        self.gn_armed = False
        self.prev_gn_armed = False
        self.prev_gn_time = 0.0

        # Publisher for Redis and HTTP
        self.publisher = Publisher()

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
                static_gesture = classify_static_gesture(hand_landmarks)
                tracker.update_pose(static_gesture, current_time)

                # Compute centroid and velocity
                centroid = compute_centroid(hand_landmarks)
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

                # Draw landmarks on frame (for debugging/preview)
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Determine which hand to use for gesture detection
            # Priority: non-steady-open hand > first hand > any hand
            active_hand_id = None
            steady_open_hand_id = None

            # Find steady open hand (potential GN modifier)
            for hand_id, hand_data in hands_data.items():
                if (
                    hand_data["pose"] == "open"
                    and hand_data["steadyMs"] >= GN_STEADY_MS
                ):
                    steady_open_hand_id = hand_id
                    break

            # Find active hand (the one performing gestures, not the modifier)
            if steady_open_hand_id:
                # Use the OTHER hand if we have a steady open modifier
                for hand_id, hand_data in hands_data.items():
                    if hand_id != steady_open_hand_id:
                        active_hand_id = hand_id
                        break
            else:
                # No modifier - use first available hand (one-hand case or both gesturing)
                active_hand_id = list(hands_data.keys())[0] if hands_data else None

            # Get gesture from active hand
            if active_hand_id and active_hand_id in hands_data:
                active_hand = hands_data[active_hand_id]
                gesture = active_hand["pose"]
                confidence = 0.85 if gesture != "idle" else 0.95

                # Track centroid from active hand for swipe detection
                for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
                    hand_label = (
                        results.multi_handedness[hand_idx].classification[0].label
                    )
                    if hand_label.lower() == active_hand_id:
                        centroid = compute_centroid(hand_landmarks)
                        cx, _ = centroid
                        self.centroid_buffer.append((current_time, cx))
                        break

            # Detect dynamic gestures (swipes) - always check
            swipe = detect_swipe(self.centroid_buffer, current_time)
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
        self.gn_armed = compute_gn_armed(
            hands_data, current_time, self.prev_gn_armed, self.prev_gn_time
        )

        # Send GN armed state if it changed
        if self.gn_armed != self.prev_gn_armed:
            await self.publisher.send_gn_armed_state(self.gn_armed)
            self.prev_gn_armed = self.gn_armed
            self.prev_gn_time = current_time

        # Always publish classified gesture data for streaming
        await self.publisher.publish_vision_intent(gesture, confidence, self.gn_armed)

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
            await self.publisher.send_command(action, payload)
            self.last_command_time = current_time

        self.last_gesture = gesture

        return frame, gesture, confidence, self.gn_armed

    async def run(self):
        """Main worker loop"""
        logger.info(f"🚀 Gesture Worker starting (ENV={ENV})...")
        logger.info(f"   Camera: {self.width}x{self.height}@{self.fps}fps")
        logger.info(f"   Redis: {REDIS_URL}")
        logger.info(f"   Control Plane: {CONTROL_PLANE_URL}")

        # Initialize publisher (Redis and HTTP clients)
        await self.publisher.initialize()

        logger.info("✅ Connected to Redis and Control Plane")

        frame_count = 0
        fps_start = time.time()
        fps_display = 0

        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning("Failed to read frame, retrying...")
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
                await self.publisher.publish_frame_snapshot(frame, current_time)

                # Show frame window (optional, disabled by default - use browser preview instead)
                if SHOW_PREVIEW_WINDOW:
                    cv2.imshow("Gesture Worker", frame)
                    if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
                        break

                # Yield control to allow other async tasks
                await asyncio.sleep(0.001)

        except KeyboardInterrupt:
            logger.info("🛑 Shutting down...")
        finally:
            self.cap.release()
            cv2.destroyAllWindows()
            await self.publisher.close()
            logger.info("✅ Cleanup complete")


if __name__ == "__main__":
    worker = GestureWorker()
    asyncio.run(worker.run())
