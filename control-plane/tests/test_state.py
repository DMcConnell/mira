import pytest
from app.core.state import State


def test_state_initialization():
    """Test that State initializes with correct defaults."""
    s = State()

    assert s.mode == "idle"
    assert s.todos == []
    assert s.mic_enabled == False
    assert s.cam_enabled == False
    assert s.last_gesture == "idle"


def test_state_apply_patch_simple():
    """Test applying simple state patches."""
    s = State()

    s.apply_patch("/mode", "voice")
    assert s.mode == "voice"

    s.apply_patch("/mic_enabled", True)
    assert s.mic_enabled == True


def test_state_apply_patch_array_append():
    """Test appending to array with + notation."""
    s = State()

    todo = {"id": 1, "text": "Test", "completed": False}
    s.apply_patch("/todos/+", todo)

    assert len(s.todos) == 1
    assert s.todos[0]["text"] == "Test"


def test_state_to_dict():
    """Test state serialization."""
    s = State()
    s.mode = "gesture"
    s.mic_enabled = True

    d = s.to_dict()

    assert d["mode"] == "gesture"
    assert d["mic_enabled"] == True
    assert "last_updated" in d
