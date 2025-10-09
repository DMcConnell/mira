"""
Command API - Proxy commands to Control Plane and fetch state.
"""

import os
import json
import aiosqlite
from typing import Any, Dict
from fastapi import APIRouter, HTTPException
import httpx

from app.models.app_wide import Command

router = APIRouter()

CONTROL_PLANE_URL = os.getenv("CONTROL_PLANE_URL", "http://localhost:8090")
DB_PATH = os.getenv("CONTROL_PLANE_DB", "/app/data/control_plane.db")


@router.post("/api/v1/command")
async def send_command(cmd: Command):
    """
    Proxy a command to the Control Plane service.
    The Control Plane will process it and broadcast state patches via Redis.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CONTROL_PLANE_URL}/command",
                json=cmd.dict(),
                timeout=5.0,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Control Plane unavailable: {str(e)}",
        )


@router.get("/api/v1/state")
async def get_state() -> Dict[str, Any]:
    """
    Get the latest state snapshot from the Control Plane database.
    Returns the most recent snapshot or an empty state if none exists.
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT state FROM snapshots ORDER BY id DESC LIMIT 1"
            )
            row = await cursor.fetchone()

            if row:
                return json.loads(row[0])
            else:
                # Return empty state if no snapshots exist yet
                return {
                    "mode": "ambient",
                    "todos": [],
                    "gesture": "idle",
                }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve state: {str(e)}",
        )
