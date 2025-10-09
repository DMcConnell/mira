from typing import Dict, Any, List
from datetime import datetime


class State:
    """
    In-memory state representation.
    This is the single source of truth that gets updated by state patches.
    """

    def __init__(self):
        self.mode = "idle"  # idle, voice, gesture, settings
        self.todos: List[Dict[str, Any]] = []
        self.mic_enabled = False
        self.cam_enabled = False
        self.last_gesture = "idle"
        self.last_updated = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "todos": self.todos,
            "mic_enabled": self.mic_enabled,
            "cam_enabled": self.cam_enabled,
            "last_gesture": self.last_gesture,
            "last_updated": self.last_updated,
        }

    def apply_patch(self, path: str, value: Any):
        """
        Apply a state patch using JSON path notation.
        Examples:
          /mode -> sets self.mode
          /todos/+ -> appends to self.todos
          /mic_enabled -> sets self.mic_enabled
        """
        parts = path.strip("/").split("/")

        if len(parts) == 1:
            # Top-level property
            if hasattr(self, parts[0]):
                setattr(self, parts[0], value)
        elif len(parts) == 2 and parts[1] == "+":
            # Array append operation
            if hasattr(self, parts[0]) and isinstance(getattr(self, parts[0]), list):
                getattr(self, parts[0]).append(value)
        elif len(parts) == 2:
            # Nested property or array index
            attr = getattr(self, parts[0], None)
            if isinstance(attr, list) and parts[1].isdigit():
                idx = int(parts[1])
                if 0 <= idx < len(attr):
                    attr[idx] = value
            elif isinstance(attr, dict):
                attr[parts[1]] = value

        self.last_updated = datetime.utcnow().isoformat()


# Global state instance
state = State()
