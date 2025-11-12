"""
Publisher module - handles Redis and HTTP publishing for gestures and commands.
"""

import base64
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import cv2
import httpx
import redis.asyncio as aioredis

from .config import (
    CONTROL_PLANE_URL,
    JPEG_QUALITY,
    REDIS_URL,
    SNAPSHOT_KEY,
    SNAPSHOT_TTL,
    VISION_CHANNEL,
    PUBLISH_REDIS,
)
from .logger import get_logger

logger = get_logger(__name__)


class Publisher:
    """Handles publishing gestures to Redis and commands to Control Plane"""

    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
        self.http_client: Optional[httpx.AsyncClient] = None
        self.last_snapshot_time = 0.0
        self.snapshot_interval = 0.1  # ~10 FPS

    async def initialize(self):
        """Initialize async clients"""
        self.redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        self.http_client = httpx.AsyncClient()

    async def close(self):
        """Close all connections"""
        if self.redis:
            await self.redis.close()
        if self.http_client:
            await self.http_client.aclose()

    def encode_frame_as_jpeg(self, frame) -> Optional[str]:
        """Encode frame as base64-encoded JPEG"""
        try:
            # Encode frame as JPEG
            success, encoded = cv2.imencode(
                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY]
            )
            if not success:
                return None
            # Convert to base64
            jpeg_bytes = encoded.tobytes()
            base64_str = base64.b64encode(jpeg_bytes).decode("utf-8")
            return base64_str
        except Exception as e:
            logger.error(f"Error encoding frame: {e}")
            return None

    async def publish_frame_snapshot(self, frame, current_time: float):
        """Publish annotated frame as base64 JPEG to Redis (throttled)"""
        if not PUBLISH_REDIS:
            return

        # Throttle to ~10 FPS
        if current_time - self.last_snapshot_time < self.snapshot_interval:
            return

        base64_jpeg = self.encode_frame_as_jpeg(frame)
        if not base64_jpeg:
            return

        try:
            # Store in Redis with TTL (will be refreshed if worker is alive)
            await self.redis.set(SNAPSHOT_KEY, base64_jpeg, ex=SNAPSHOT_TTL)
            self.last_snapshot_time = current_time
        except Exception as e:
            logger.error(f"Error publishing frame snapshot: {e}")

    async def publish_vision_intent(
        self, gesture: str, confidence: float, gn_armed: bool
    ):
        """Publish classified gesture data to Redis for real-time streaming"""
        if not PUBLISH_REDIS:
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
            logger.error(f"Error publishing vision intent: {e}")

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
            logger.error(f"Error sending GN armed state: {e}")

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
            logger.info(f"✓ Command sent: {action}")
        except Exception as e:
            logger.error(f"Error sending command: {e}")
