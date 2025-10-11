from fastapi import APIRouter, Depends

from app.models.app_wide import Settings
from app.util.auth import require_capability, TokenData

router = APIRouter()

# In-memory settings storage (module-level variable)
_settings = Settings()


@router.get("/api/v1/settings", response_model=Settings)
async def get_settings(token: TokenData = Depends(require_capability("command.send"))):
    """Get current settings. Requires 'command.send' capability."""
    return _settings


@router.put("/api/v1/settings", response_model=Settings)
async def update_settings(
    settings: Settings, token: TokenData = Depends(require_capability("command.send"))
):
    """Update settings. Requires 'command.send' capability."""
    global _settings
    _settings = settings
    return _settings


def get_current_settings() -> Settings:
    """Helper function to get current settings for use by other modules."""
    return _settings
