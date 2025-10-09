"""
EXAMPLE: Protected Command API with JWT Authentication

This is an example showing how to protect the command endpoint.
To enable this, replace the content in command.py with this code.

BEFORE using this:
1. Generate strong secrets (see SECURITY_GUIDE.md)
2. Set JWT_SECRET and MIRA_PIN environment variables
3. Update frontend to send JWT tokens in Authorization header
"""

import os
import json
import aiosqlite
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends
import httpx

from app.models.app_wide import Command
from app.util.auth import require_capability, optional_auth, TokenData

router = APIRouter()

CONTROL_PLANE_URL = os.getenv("CONTROL_PLANE_URL", "http://localhost:8090")
DB_PATH = os.getenv("CONTROL_PLANE_DB", "/app/data/control_plane.db")


@router.post("/api/v1/command")
async def send_command(
    cmd: Command,
    token: TokenData = Depends(require_capability("command.send")),
):
    """
    🔒 PROTECTED: Proxy a command to the Control Plane service.

    Requires:
        - Valid JWT token in Authorization header
        - Token must have "command.send" capability

    Headers:
        Authorization: Bearer <jwt_token>

    The Control Plane will process it and broadcast state patches via Redis.
    """
    # Log who sent the command (useful for audit)
    print(f"Command from authenticated user with caps: {token.capabilities}")

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

    NOTE: This endpoint is PUBLIC (no authentication required).
    If you want to protect it, add: token: TokenData = Depends(verify_token)

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


# Example: Endpoint with optional authentication
@router.get("/api/v1/state/enhanced")
async def get_enhanced_state(
    token: Optional[TokenData] = Depends(optional_auth),
) -> Dict[str, Any]:
    """
    Example endpoint that provides different responses based on authentication.

    - Authenticated users: Get full state with sensitive data
    - Unauthenticated users: Get limited public state
    """
    state = await get_state()

    if token:
        # User is authenticated, return full state
        return {
            **state,
            "sensitive_data": "Only visible to authenticated users",
            "user_capabilities": token.capabilities,
        }
    else:
        # User is not authenticated, return limited state
        return {
            "mode": state.get("mode"),
            "public_info": "Limited view for unauthenticated access",
        }
