from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

# Path to static snapshot image
STATIC_DIR = Path(__file__).parent.parent / "static"
SNAPSHOT_PATH = STATIC_DIR / "sample.jpg"


@router.get("/vision/snapshot.jpg")
async def get_vision_snapshot():
    """
    Get the current vision snapshot image.
    In mock mode, returns a static sample image.
    """
    if SNAPSHOT_PATH.exists():
        return FileResponse(
            SNAPSHOT_PATH,
            media_type="image/jpeg",
            headers={"Cache-Control": "no-cache"},
        )
    else:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Snapshot image not found")
