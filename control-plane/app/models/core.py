from pydantic import BaseModel, Field
from typing import Literal, Dict, Any
from datetime import datetime
import uuid


class Command(BaseModel):
    """
    Command represents an input from voice, gesture, or system sources.
    It gets processed by the Arbiter to generate Events.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ts: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    source: Literal["voice", "gesture", "system"]
    action: str
    payload: Dict[str, Any] = {}


class Event(BaseModel):
    """
    Event represents the outcome of processing a Command.
    Events are persisted to SQLite for audit and replay.
    """

    id: str
    ts: str
    commandId: str
    type: Literal["accepted", "rejected", "state_patch"]
    payload: Dict[str, Any]


class StatePatch(BaseModel):
    """
    StatePatch represents a change to the application state.
    These are broadcast via Redis Pub/Sub to all subscribers.
    """

    ts: str
    path: str  # JSON path notation, e.g., "/todos/+", "/mode"
    value: Any
