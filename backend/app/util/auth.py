"""
JWT Authentication Middleware and Dependencies

Usage:
    from app.util.auth import verify_token, require_capability

    # Simple JWT verification
    @app.get("/protected")
    async def protected(token: TokenData = Depends(verify_token)):
        return {"user_caps": token.capabilities}

    # Require specific capability
    @app.post("/command")
    async def send_command(
        cmd: Command,
        token: TokenData = Depends(require_capability("command.send"))
    ):
        # User has "command.send" capability
        return {"status": "ok"}
"""

import os
from typing import List, Optional

import jwt
from fastapi import HTTPException, Header, Depends
from pydantic import BaseModel

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
ALGORITHM = "HS256"


class TokenData(BaseModel):
    """Parsed JWT token data"""

    capabilities: List[str]
    exp: int
    iat: int


async def verify_token(authorization: Optional[str] = Header(None)) -> TokenData:
    """
    Dependency that verifies JWT token from Authorization header.
    Raises 401 if token is missing, expired, or invalid.

    Args:
        authorization: Authorization header value (format: "Bearer <token>")

    Returns:
        TokenData with capabilities and metadata

    Raises:
        HTTPException: 401 if authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(
            capabilities=payload.get("cap", []),
            exp=payload["exp"],
            iat=payload["iat"],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_capability(required_cap: str):
    """
    Dependency factory that checks for a specific capability.
    Returns a dependency function that can be used with Depends().

    Args:
        required_cap: The capability string to check for (e.g., "command.send")

    Returns:
        Dependency function that verifies token and checks capability

    Example:
        @app.post("/command")
        async def send_command(
            cmd: Command,
            token: TokenData = Depends(require_capability("command.send"))
        ):
            # User has "command.send" capability
            pass
    """

    async def capability_checker(
        token: TokenData = Depends(verify_token),
    ) -> TokenData:
        if required_cap not in token.capabilities:
            raise HTTPException(
                status_code=403,
                detail=f"Missing required capability: {required_cap}",
            )
        return token

    return capability_checker


async def optional_auth(
    authorization: Optional[str] = Header(None),
) -> Optional[TokenData]:
    """
    Optional authentication dependency.
    Returns TokenData if valid token is provided, None otherwise.
    Does not raise exceptions for missing/invalid tokens.

    Useful for endpoints that want to provide different behavior for authenticated users
    but don't strictly require authentication.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(
            capabilities=payload.get("cap", []),
            exp=payload["exp"],
            iat=payload["iat"],
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
