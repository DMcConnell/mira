import pytest
import asyncio
from app.models.core import Command
from app.core.arbiter import handle_command
from app.services.db import init_db


@pytest.fixture
async def setup_db():
    """Initialize database before tests."""
    await init_db()
    yield


@pytest.mark.asyncio
async def test_add_todo_command(setup_db):
    """Test that add_todo command generates state_patch event."""
    cmd = Command(source="voice", action="add_todo", payload={"text": "Test todo"})

    event = await handle_command(cmd)

    assert event.type == "state_patch"
    assert event.commandId == cmd.id
    assert "path" in event.payload
    assert event.payload["path"] == "/todos/+"


@pytest.mark.asyncio
async def test_toggle_mic_command(setup_db):
    """Test that toggle_mic command generates state_patch event."""
    cmd = Command(source="gesture", action="toggle_mic", payload={})

    event = await handle_command(cmd)

    assert event.type == "state_patch"
    assert event.payload["path"] == "/mic_enabled"


@pytest.mark.asyncio
async def test_unknown_command_rejected(setup_db):
    """Test that unknown commands are rejected."""
    cmd = Command(source="system", action="unknown_action", payload={})

    event = await handle_command(cmd)

    assert event.type == "rejected"
    assert event.payload["reason"] == "unknown_action"
