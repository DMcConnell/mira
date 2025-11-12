"""
Configuration constants and environment variables for the gesture worker.
"""

import os

# Gesture detection thresholds
GN_STEADY_MS = 250  # steady open hand duration for GN armed
GN_HYSTERESIS_MS = 120  # prevent flicker in GN armed state
PINCH_THRESHOLD = 0.05  # normalized distance threshold for pinch detection

# Swipe detection thresholds
SWIPE_MIN_DISPLACEMENT = 0.25  # 25% of screen width
SWIPE_MIN_DURATION = 0.50  # at least 500ms
SWIPE_MAX_DURATION = 2.00  # no more than 2s

# Environment configuration
ENV = os.getenv("MIRA_ENV", "mac")  # "mac" or "pi"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CONTROL_PLANE_URL = os.getenv("CONTROL_PLANE_URL", "http://localhost:8090")
SHOW_PREVIEW_WINDOW = os.getenv("SHOW_PREVIEW_WINDOW", "false").lower() == "true"

# Redis channels and keys
PUBLISH_REDIS = os.getenv("PUBLISH_REDIS", "true").lower() == "true"
VISION_CHANNEL = "mira:vision"  # Redis channel for raw vision data
SNAPSHOT_KEY = "mira:vision:snapshot"  # Redis key for latest frame snapshot

# MediaPipe configuration
MEDIAPIPE_MODEL_COMPLEXITY = 1
MEDIAPIPE_MAX_NUM_HANDS = 2
MEDIAPIPE_MIN_DETECTION_CONFIDENCE = 0.4
MEDIAPIPE_MIN_TRACKING_CONFIDENCE = 0.4

# Frame processing configuration
SNAPSHOT_INTERVAL = 0.1  # ~10 FPS for frame snapshots
SNAPSHOT_TTL = 2  # seconds TTL for snapshot in Redis
JPEG_QUALITY = 80  # JPEG encoding quality (0-100)

# Command debouncing
COMMAND_COOLDOWN_DURATION = 0.5  # seconds between commands

# Default camera settings
DEFAULT_WIDTH = 640
DEFAULT_HEIGHT = 360
DEFAULT_FPS = 30
