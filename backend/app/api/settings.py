from fastapi import APIRouter

from app.models.global_dto import Settings

router = APIRouter()

# In-memory settings storage (module-level variable)
_settings = Settings()


@router.get("/api/v1/settings", response_model=Settings)
async def get_settings():
    """Get current settings."""
    return _settings


@router.put("/api/v1/settings", response_model=Settings)
async def update_settings(settings: Settings):
    """Update settings."""
    global _settings
    _settings = settings
    return _settings


def get_current_settings() -> Settings:
    """Helper function to get current settings for use by other modules."""
    return _settings
