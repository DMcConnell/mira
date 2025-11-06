from typing import Dict, Any, List
from datetime import datetime


class State:
    """
    In-memory state representation.
    This is the single source of truth that gets updated by state patches.
    Includes UIState for Phase A & B.
    """

    def __init__(self):
        # Legacy mode (kept for backward compatibility)
        self.mode = "idle"  # idle, voice, gesture, settings
        self.todos: List[Dict[str, Any]] = []
        self.mic_enabled = False
        self.cam_enabled = False
        self.last_gesture = "idle"
        self.last_updated = datetime.utcnow().isoformat()

        # UIState (Phase A & B)
        self.ui_mode = "public"  # "public" | "private"
        self.app_route = "home"  # "home" | "weather" | "email" | "finance" | "news" | "todos" | "calendar" | "settings"
        self.focus_path: List[str] = []
        self.gn_armed = False
        self.debug_enabled = False
        self.hud = {
            "micOn": False,
            "camOn": False,
            "wsConnected": False,
            "wake": False,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "todos": self.todos,
            "mic_enabled": self.mic_enabled,
            "cam_enabled": self.cam_enabled,
            "last_gesture": self.last_gesture,
            "last_updated": self.last_updated,
            # UIState
            "ui": {
                "mode": self.ui_mode,
                "appRoute": self.app_route,
                "focusPath": self.focus_path,
                "gnArmed": self.gn_armed,
                "debug": {"enabled": self.debug_enabled},
                "hud": self.hud,
            },
        }

    def apply_patch(self, path: str, value: Any):
        """
        Apply a state patch using JSON path notation.
        Examples:
          /mode -> sets self.mode
          /todos/+ -> appends to self.todos
          /mic_enabled -> sets self.mic_enabled
          /ui/mode -> sets self.ui_mode
          /ui/appRoute -> sets self.app_route
          /ui/gnArmed -> sets self.gn_armed
        """
        parts = path.strip("/").split("/")

        # Handle UI state paths
        if len(parts) >= 2 and parts[0] == "ui":
            if parts[1] == "mode":
                self.ui_mode = value
            elif parts[1] == "appRoute":
                self.app_route = value
            elif parts[1] == "focusPath":
                self.focus_path = value if isinstance(value, list) else []
            elif parts[1] == "gnArmed":
                self.gn_armed = value
            elif parts[1] == "debug" and len(parts) >= 3:
                if parts[2] == "enabled":
                    self.debug_enabled = value
            elif parts[1] == "hud" and len(parts) >= 3:
                if parts[2] in self.hud:
                    self.hud[parts[2]] = value
            return

        # Handle legacy paths
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
