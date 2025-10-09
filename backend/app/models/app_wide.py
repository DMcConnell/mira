from pydantic import BaseModel, Field
from typing import Literal, Dict, Any
from datetime import datetime
import uuid


class VisionIntent(BaseModel):
    tsISO: str
    gesture: str
    confidence: float
    armed: bool


class Settings(BaseModel):
    weatherMode: str = "mock"
    newsMode: str = "mock"


class Command(BaseModel):
    """Command to be sent to the Control Plane"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    source: Literal["voice", "gesture", "system"]
    action: str
    payload: Dict[str, Any] = {}


class StatePatch(BaseModel):
    """State patch received from Control Plane via Redis"""

    ts: str
    path: str
    value: Any
