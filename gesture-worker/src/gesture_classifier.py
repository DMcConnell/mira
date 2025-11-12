"""
Gesture classification module - detects static gestures, swipes, and computes GN armed state.
"""

from collections import deque
from .logger import get_logger
from typing import Deque, Dict, Optional, Tuple

import numpy as np

from .config import (
    GN_HYSTERESIS_MS,
    GN_STEADY_MS,
    PINCH_THRESHOLD,
    SWIPE_MAX_DURATION,
    SWIPE_MIN_DISPLACEMENT,
    SWIPE_MIN_DURATION,
)

# Logger
logger = get_logger()


def compute_centroid(landmarks) -> Tuple[float, float]:
    """Compute normalized (x, y) centroid of hand"""
    xs = [lm.x for lm in landmarks.landmark]
    ys = [lm.y for lm in landmarks.landmark]
    return float(np.mean(xs)), float(np.mean(ys))


def compute_distance(p1, p2) -> float:
    """Compute normalized distance between two points"""
    dx = p1.x - p2.x
    dy = p1.y - p2.y
    return np.sqrt(dx * dx + dy * dy)


def classify_static_gesture(landmarks) -> str:
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

    logger.info(
        f"index finger - extended: {idx_extended}; idx_tip.y: {idx_tip.y}; idx_pip.y: {idx_pip.y}"
    )
    logger.info(
        f"middle finger - extended: {mid_extended}; mid_tip.y: {mid_tip.y}; mid_pip.y: {mid_pip.y}"
    )
    logger.info(
        f"ring finger - extended: {ring_extended}; ring_tip.y: {ring_tip.y}; ring_pip.y: {ring_pip.y}"
    )
    logger.info(
        f"pinky finger - extended: {pinky_extended}; pinky_tip.y: {pinky_tip.y}; pinky_pip.y: {pinky_pip.y}"
    )
    logger.info(
        f"thumb - extended: {thumb_extended}; thumb_tip.x: {thumb_tip.x}; thumb_ip.x: {thumb_ip.x}"
    )

    # Check for pinch (thumb and index tip close together)
    pinch_distance = compute_distance(thumb_tip, idx_tip)
    is_pinch = pinch_distance < PINCH_THRESHOLD

    # Check for two-finger (index and middle extended, others closed)
    is_two_finger = idx_extended and mid_extended and not any(fingers_extended[2:])

    # Classify
    if is_pinch and not idx_extended:
        return "pinch"
    elif is_two_finger:
        return "twoFinger"
    elif all(fingers_extended):  # Ignore thumb as it could go either direction
        return "open"
    elif not any(fingers_extended):  # Ignore thumb as it could go either direction
        return "fist"
    else:
        return "unknown"


def detect_swipe(
    centroid_buffer: Deque[Tuple[float, float]], current_time: float
) -> Optional[str]:
    """
    Detect horizontal swipe gestures from centroid buffer.
    Returns: 'swipe_left', 'swipe_right', or None
    """
    if len(centroid_buffer) < 8:
        return None

    t0, x0 = centroid_buffer[0]
    t1, x1 = centroid_buffer[-1]

    dx = x1 - x0
    duration = t1 - t0

    if (
        duration > SWIPE_MIN_DURATION
        and duration < SWIPE_MAX_DURATION
        and abs(dx) > SWIPE_MIN_DISPLACEMENT
    ):
        if dx > 0:
            return "swipe_right"
        else:
            return "swipe_left"

    return None


def compute_gn_armed(
    hands_data: Dict[str, Dict],
    current_time: float,
    prev_gn_armed: bool,
    prev_gn_time: float,
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
        if not prev_gn_armed:
            # Apply hysteresis: require 250ms steady before arming
            if hands_data[steady_hand]["steadyMs"] >= GN_STEADY_MS:
                return True
        else:
            # Already armed - apply hysteresis to prevent flicker
            if hands_data[steady_hand]["steadyMs"] < (GN_STEADY_MS - GN_HYSTERESIS_MS):
                return False
            return True

    # Disarm if no steady hand or both hands gesturing
    if prev_gn_armed:
        # Hysteresis: keep armed for 120ms after condition fails
        if (current_time - prev_gn_time) * 1000 < GN_HYSTERESIS_MS:
            return True

    return False
