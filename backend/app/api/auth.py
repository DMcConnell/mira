"""
Auth API - PIN-based authentication with JWT tokens.
"""

import os
from datetime import datetime, timedelta
from typing import List

import jwt
from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel

router = APIRouter()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
ALGORITHM = "HS256"
MIRA_PIN = os.getenv("MIRA_PIN", "1234")


class TokenResponse(BaseModel):
    """Response model for authentication"""

    token: str
    capabilities: List[str]


@router.post("/auth/pin", response_model=TokenResponse)
async def pin_login(pin: str = Form(...)):
    """
    Authenticate using PIN and receive a JWT token.
    The token includes capabilities (permissions) for the user.

    Default PIN: 1234 (set via MIRA_PIN environment variable)
    """
    if pin != MIRA_PIN:
        raise HTTPException(
            status_code=401,
            detail="Invalid PIN",
        )

    # Create JWT with capabilities
    payload = {
        "cap": ["mic.toggle", "cam.toggle", "mode.switch", "command.send"],
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return TokenResponse(
        token=token,
        capabilities=payload["cap"],
    )


@router.post("/auth/verify")
async def verify_token(token: str = Form(...)):
    """
    Verify a JWT token and return its capabilities.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {
            "valid": True,
            "capabilities": payload.get("cap", []),
            "expires": payload.get("exp"),
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )
