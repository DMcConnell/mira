# Mira Authentication & Security Guide

## Overview

This guide explains the authentication system and how to secure your Mira installation.

## Authentication Flow

```
┌─────────┐     PIN      ┌─────────┐     JWT      ┌──────────────┐
│ User UI │ ──────────> │ Backend │ ──────────> │ Control Plane│
└─────────┘             └─────────┘              └──────────────┘
     │                       │                          │
     │  1. Enter PIN (1234)  │                          │
     │ ───────────────────>  │                          │
     │                       │ Validate PIN             │
     │                       │ Generate JWT             │
     │  2. Receive JWT       │                          │
     │ <───────────────────  │                          │
     │                       │                          │
     │  3. Send Command      │                          │
     │    with JWT header    │                          │
     │ ───────────────────>  │                          │
     │                       │ Verify JWT               │
     │                       │ Check capabilities       │
     │                       │  4. Proxy Command        │
     │                       │ ──────────────────────>  │
```

## Current State (Phase 2)

### ✅ Implemented

- PIN authentication endpoint
- JWT token generation
- Capability-based permissions in token
- Token verification endpoint

### ❌ Missing (Security Gaps)

- JWT verification middleware on protected endpoints
- Token storage and usage in frontend
- Secure secret management
- Token refresh mechanism
- Rate limiting on auth endpoints

## Step-by-Step Security Hardening

### 1. Generate Strong Secrets

**Never use default secrets in production!**

```bash
# Generate a strong JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# Example output: 8kZx3Qa_pM5tNnL2jR6vYw9bC4fDhG1eS7uT0iK8mP4

# Choose a secure PIN (4-6 digits minimum)
# Example: 8472, 194856
```

### 2. Set Environment Variables

**Development (.env file)**

```bash
# backend/.env
JWT_SECRET=your-generated-secret-here
MIRA_PIN=8472
```

**Production (Docker Compose)**

```yaml
# docker-compose.yml
services:
  server:
    environment:
      - JWT_SECRET=${JWT_SECRET} # Set in host environment
      - MIRA_PIN=${MIRA_PIN} # Set in host environment
```

**On Raspberry Pi**

```bash
# /etc/environment or systemd service file
export JWT_SECRET="your-secret-here"
export MIRA_PIN="8472"
```

### 3. Add JWT Verification Middleware

Create `backend/app/util/auth.py`:

```python
"""
JWT Authentication Middleware and Dependencies
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

    Usage:
        @app.get("/protected")
        async def protected_route(token: TokenData = Depends(verify_token)):
            # token.capabilities contains user permissions
            pass
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization header format. Use: Bearer <token>",
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
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )


def require_capability(required_cap: str):
    """
    Dependency that checks for a specific capability.

    Usage:
        @app.post("/command")
        async def send_command(
            cmd: Command,
            token: TokenData = Depends(require_capability("command.send"))
        ):
            # User has "command.send" capability
            pass
    """
    async def capability_checker(token: TokenData = Depends(verify_token)) -> TokenData:
        if required_cap not in token.capabilities:
            raise HTTPException(
                status_code=403,
                detail=f"Missing required capability: {required_cap}",
            )
        return token

    return capability_checker
```

### 4. Protect Your Endpoints

**Before (Unsecured):**

```python
@router.post("/api/v1/command")
async def send_command(cmd: Command):
    # Anyone can call this!
    ...
```

**After (Secured):**

```python
from app.util.auth import require_capability, TokenData

@router.post("/api/v1/command")
async def send_command(
    cmd: Command,
    token: TokenData = Depends(require_capability("command.send"))
):
    # Only authenticated users with "command.send" capability can call this
    ...
```

### 5. Update All Protected Endpoints

**Endpoints that SHOULD be protected:**

- `POST /api/v1/command` - Requires `command.send`
- `POST /api/v1/todos` - Requires `command.send`
- `PUT /api/v1/todos/{id}` - Requires `command.send`
- `DELETE /api/v1/todos/{id}` - Requires `command.send`
- `PUT /api/v1/settings` - Requires `settings.edit`

**Endpoints that should be PUBLIC:**

- `POST /auth/pin` - Login endpoint
- `GET /health` - Health check
- `GET /api/v1/morning-report` - Read-only data
- `GET /api/v1/todos` - Read-only data
- `GET /api/v1/state` - Read-only data
- `WS /ws/state` - Real-time updates (can optionally protect)
- `WS /ws/vision` - Real-time updates (can optionally protect)

### 6. Frontend Token Storage

**Update `frontend/src/lib/auth.ts`** (new file):

```typescript
const TOKEN_KEY = 'mira_token';

export const authService = {
  // Store token in localStorage
  setToken(token: string) {
    localStorage.setItem(TOKEN_KEY, token);
  },

  // Get stored token
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  // Remove token (logout)
  clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  },

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return this.getToken() !== null;
  },
};
```

**Update `frontend/src/lib/api.ts`:**

```typescript
import { authService } from './auth';

// Add token to all requests
api.interceptors.request.use((config) => {
  const token = authService.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses (token expired)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      authService.clearToken();
      // Optionally redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  },
);
```

**Add Login Flow:**

```typescript
// Login with PIN
export const login = async (pin: string) => {
  const formData = new FormData();
  formData.append('pin', pin);

  const response = await api.post('/auth/pin', formData);
  const { token } = response.data;

  authService.setToken(token);
  return response.data;
};
```

### 7. Update Capabilities (Optional)

Customize what users can do by modifying capabilities in `backend/app/api/auth.py`:

```python
# Current capabilities
payload = {
    "cap": [
        "mic.toggle",
        "cam.toggle",
        "mode.switch",
        "command.send",
        "settings.edit",  # Add this
    ],
    ...
}
```

You could even support **multiple PINs** with different permission levels:

```python
# Example: Different roles
ADMIN_PIN = os.getenv("MIRA_ADMIN_PIN")
USER_PIN = os.getenv("MIRA_USER_PIN")

if pin == ADMIN_PIN:
    capabilities = ["admin", "command.send", "settings.edit", "mic.toggle", "cam.toggle"]
elif pin == USER_PIN:
    capabilities = ["command.send"]  # Limited permissions
else:
    raise HTTPException(401, "Invalid PIN")
```

## Security Best Practices

### ✅ DO

1. **Use strong, random secrets**

   - JWT_SECRET: 32+ characters, random
   - PIN: 6+ digits minimum

2. **Set secrets via environment variables**

   - Never commit secrets to git
   - Use `.env` files (add to `.gitignore`)
   - Use secret management in production (AWS Secrets Manager, etc.)

3. **Protect sensitive endpoints**

   - Require JWT for write operations
   - Check capabilities before allowing actions

4. **Use HTTPS in production**

   - Never send tokens over HTTP
   - Configure nginx/caddy with SSL

5. **Implement rate limiting**

   - Limit PIN attempts (3-5 per minute)
   - Prevent brute force attacks

6. **Rotate secrets periodically**
   - Change JWT_SECRET every 90 days
   - Change PIN if compromised

### ❌ DON'T

1. **Don't use default secrets**

   - `dev-secret-change-in-production` is NOT secure
   - `1234` is easily guessed

2. **Don't commit secrets**

   - Add `.env` to `.gitignore`
   - Don't hardcode secrets in code

3. **Don't expose tokens in logs**

   - Sanitize logs to remove tokens
   - Don't log request headers

4. **Don't store tokens in insecure places**
   - localStorage is OK for this use case (mirror in home)
   - Cookies with httpOnly would be more secure

## Production Deployment Checklist

- [ ] Generate strong JWT_SECRET
- [ ] Set secure MIRA_PIN (6+ digits)
- [ ] Add JWT verification middleware
- [ ] Protect all write endpoints
- [ ] Implement frontend token storage
- [ ] Enable HTTPS/TLS
- [ ] Add rate limiting on /auth/pin
- [ ] Remove default secrets from code
- [ ] Test authentication flow end-to-end
- [ ] Set up secret rotation plan
- [ ] Configure firewall rules
- [ ] Review CORS settings (restrict origins)

## Testing Authentication

```bash
# 1. Login and get token
TOKEN=$(curl -X POST http://localhost:8080/auth/pin \
  -d "pin=8472" | jq -r .token)

# 2. Use token in requests
curl -X POST http://localhost:8080/api/v1/command \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "system",
    "action": "add_todo",
    "payload": {"text": "Authenticated todo"}
  }'

# 3. Try without token (should fail with 401)
curl -X POST http://localhost:8080/api/v1/command \
  -H "Content-Type: application/json" \
  -d '{"source": "system", "action": "test"}'
```

## Additional Security Layers (Advanced)

### 1. Rate Limiting

Use `slowapi` or `fastapi-limiter`:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/auth/pin")
@limiter.limit("5/minute")  # Max 5 attempts per minute
async def pin_login(request: Request, pin: str = Form(...)):
    ...
```

### 2. Token Refresh

Implement short-lived access tokens + long-lived refresh tokens:

- Access token: 15 minutes
- Refresh token: 7 days
- Endpoint: `POST /auth/refresh`

### 3. Multi-Factor Authentication

Add a second factor:

- TOTP (Google Authenticator)
- Hardware key (U2F/WebAuthn)
- Biometric on mobile

### 4. Audit Logging

Log all authentication attempts:

```python
logger.info(f"Login attempt from {request.client.host} - {'success' if valid else 'failed'}")
```

## Questions?

- **Q: Do I need auth for a private home mirror?**

  - A: It depends. If only you use it on your home network, basic PIN + HTTPS may be enough.

- **Q: What if I expose this to the internet?**

  - A: You MUST implement all security measures, especially HTTPS, strong secrets, and rate limiting.

- **Q: Can I disable auth for local development?**

  - A: Yes, but use environment variables to enable/disable, don't remove the code.

- **Q: Should WebSocket connections be authenticated?**
  - A: For public deployments, yes. Pass token as query param: `ws://...?token=<jwt>`
