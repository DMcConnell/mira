import base64
import os
from pathlib import Path

import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

router = APIRouter()

# Path to static snapshot image
STATIC_DIR = Path(__file__).parent.parent / "static"
SNAPSHOT_PATH = STATIC_DIR / "sample.jpg"

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
SNAPSHOT_KEY = "mira:vision:snapshot"

# Redis client (lazy initialization)
_redis_client: aioredis.Redis | None = None


async def get_redis_client() -> aioredis.Redis:
    """Get or create Redis client"""
    global _redis_client
    if _redis_client is None:
        _redis_client = await aioredis.from_url(REDIS_URL, decode_responses=False)
    return _redis_client


@router.get("/vision/snapshot.jpg")
async def get_vision_snapshot():
    """
    Get the current vision snapshot image.
    Reads from Redis if available, otherwise falls back to static sample image.
    """
    try:
        redis_client = await get_redis_client()
        base64_jpeg = await redis_client.get(SNAPSHOT_KEY)

        if base64_jpeg:
            # Decode base64 JPEG
            try:
                # Redis returns bytes when decode_responses=False, decode to string first
                base64_str = base64_jpeg.decode('utf-8')
                jpeg_bytes = base64.b64decode(base64_str)
                return Response(
                    content=jpeg_bytes,
                    media_type="image/jpeg",
                    headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
                )
            except Exception as e:
                print(f"Error decoding snapshot from Redis: {e}")
                # Fall through to fallback

        # Fallback to static sample image
        if SNAPSHOT_PATH.exists():
            return FileResponse(
                SNAPSHOT_PATH,
                media_type="image/jpeg",
                headers={"Cache-Control": "no-cache"},
            )
        else:
            raise HTTPException(status_code=404, detail="Snapshot image not found")

    except Exception as e:
        print(f"Error getting vision snapshot: {e}")
        # Fallback to static sample image if available
        if SNAPSHOT_PATH.exists():
            return FileResponse(
                SNAPSHOT_PATH,
                media_type="image/jpeg",
                headers={"Cache-Control": "no-cache"},
            )
        raise HTTPException(status_code=404, detail="Snapshot image not found")
