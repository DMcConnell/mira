# Authentication Quick Start Guide

## Current State (What's Implemented)

✅ **Backend has authentication infrastructure:**

- `POST /auth/pin` - Login endpoint that issues JWT tokens
- JWT tokens contain capabilities (permissions)
- Tokens expire after 24 hours
- Helper middleware ready to use (`app/util/auth.py`)

❌ **But it's NOT enforced yet:**

- Endpoints are still accessible without authentication
- Frontend doesn't store or send tokens
- Using default/weak secrets

## How It Works (Simple Explanation)

```
1. User enters PIN (1234) → Frontend sends to /auth/pin
2. Backend validates PIN → Returns JWT token
3. Frontend stores token → Includes in all requests
4. Backend checks token → Allows/denies access
```

## What You Need to Do

### For Development (Now)

**Just test the PIN login:**

```bash
# Login and get a token
curl -X POST http://localhost:8080/auth/pin -d "pin=1234"

# Returns:
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "capabilities": ["mic.toggle", "cam.toggle", "mode.switch", "command.send"]
}
```

The token contains your permissions but **nothing checks it yet**.

### For Production (Before Deploying)

Follow these 3 steps:

#### 1. Generate Strong Secrets (5 minutes)

```bash
# Generate JWT secret
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Copy output and add to docker-compose.yml:
services:
  server:
    environment:
      - JWT_SECRET=<paste-generated-secret-here>
      - MIRA_PIN=8472  # Choose your own 4-6 digit PIN
```

#### 2. Protect Endpoints (10 minutes)

**Edit `backend/app/api/command.py`:**

```python
# Add this import at the top
from app.util.auth import require_capability, TokenData

# Change this:
@router.post("/api/v1/command")
async def send_command(cmd: Command):
    ...

# To this:
@router.post("/api/v1/command")
async def send_command(
    cmd: Command,
    token: TokenData = Depends(require_capability("command.send"))
):
    ...
```

**Same for todos.py:**

```python
from app.util.auth import require_capability, TokenData

@router.post("/api/v1/todos")
async def create_todo(
    todo_text: str,
    token: TokenData = Depends(require_capability("command.send"))
):
    ...

@router.put("/api/v1/todos/{id}")
async def update_todo(
    id: str,
    updates: dict,
    token: TokenData = Depends(require_capability("command.send"))
):
    ...
```

See `command_protected_example.py` for full example.

#### 3. Update Frontend (15 minutes)

**Create `frontend/src/lib/auth.ts`:**

```typescript
const TOKEN_KEY = 'mira_token';

export const authService = {
  setToken(token: string) {
    localStorage.setItem(TOKEN_KEY, token);
  },

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  },

  isAuthenticated(): boolean {
    return this.getToken() !== null;
  },
};

export const login = async (pin: string) => {
  const formData = new FormData();
  formData.append('pin', pin);

  const response = await fetch('/auth/pin', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) throw new Error('Invalid PIN');

  const data = await response.json();
  authService.setToken(data.token);
  return data;
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
```

## Do I Need This for a Home Mirror?

**Short answer:** Not immediately, but recommended.

**If your mirror is:**

- ✅ Only on your home WiFi
- ✅ Not exposed to internet
- ✅ Only you use it

→ You can use default PIN (1234) for now, but **change JWT_SECRET**.

**If your mirror will:**

- ❌ Be exposed to internet
- ❌ Be accessible by multiple people
- ❌ Control sensitive devices

→ You MUST implement all security measures immediately.

## Testing

**Test with authentication:**

```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost:8080/auth/pin -d "pin=1234" | jq -r .token)

# 2. Use token
curl -X POST http://localhost:8080/api/v1/command \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source":"system","action":"test"}'

# 3. Try without token (should fail with 401 if protected)
curl -X POST http://localhost:8080/api/v1/command \
  -H "Content-Type: application/json" \
  -d '{"source":"system","action":"test"}'
```

## Environment Variables Summary

```bash
# Required for production
JWT_SECRET=<generated-secret>    # 32+ random characters
MIRA_PIN=<your-pin>              # 4-6 digits

# Optional
JWT_ALGORITHM=HS256              # Default is fine
TOKEN_EXPIRY_HOURS=24            # Default is fine
```

## Files Created

- ✅ `app/util/auth.py` - JWT verification middleware (ready to use)
- ✅ `app/api/auth.py` - Login endpoints (already working)
- 📖 `SECURITY_GUIDE.md` - Complete security documentation
- 📖 `command_protected_example.py` - Example protected endpoint

## Next Steps

1. **Now:** Test the PIN login works
2. **Before prod:** Change secrets, protect endpoints
3. **Optional:** Add frontend login page

## Questions?

**Q: What if I forget my PIN?**
A: Change MIRA_PIN environment variable and restart

**Q: Can I have multiple users?**
A: Yes! See "Multiple PINs" section in SECURITY_GUIDE.md

**Q: Do WebSockets need auth?**
A: Not critical for home use, but yes for public deployment

**Q: Token expired, what happens?**
A: Frontend gets 401, needs to login again (auto-redirect recommended)

For more details, see `SECURITY_GUIDE.md`
