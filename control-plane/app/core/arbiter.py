from ..models.core import Command, Event, StatePatch
from ..services.bus import publish_state
from .state import state
import json
import aiosqlite
from datetime import datetime


async def handle_command(cmd: Command) -> Event:
    """
    Arbiter processes commands and generates events.
    Applies policy rules and reduces commands into state patches.
    """
    print(f"Processing command: {cmd.action} from {cmd.source}")

    # Policy: Add todo
    if cmd.action.startswith("add_todo"):
        patch = StatePatch(
            ts=cmd.ts,
            path="/todos/+",
            value={
                "id": len(state.todos) + 1,
                "text": cmd.payload.get("text", ""),
                "completed": False,
                "created_at": cmd.ts,
            },
        )
        event = Event(
            id=cmd.id,
            ts=cmd.ts,
            commandId=cmd.id,
            type="state_patch",
            payload=patch.dict(),
        )

        # Apply patch locally
        state.apply_patch(patch.path, patch.value)

        # Persist and broadcast
        await persist_event(event)
        await publish_state(patch.dict())
        return event

    # Policy: Toggle mic
    elif cmd.action == "toggle_mic":
        new_state = not state.mic_enabled
        patch = StatePatch(ts=cmd.ts, path="/mic_enabled", value=new_state)
        event = Event(
            id=cmd.id,
            ts=cmd.ts,
            commandId=cmd.id,
            type="state_patch",
            payload=patch.dict(),
        )

        state.apply_patch(patch.path, patch.value)
        await persist_event(event)
        await publish_state(patch.dict())
        return event

    # Policy: Toggle camera
    elif cmd.action == "toggle_cam":
        new_state = not state.cam_enabled
        patch = StatePatch(ts=cmd.ts, path="/cam_enabled", value=new_state)
        event = Event(
            id=cmd.id,
            ts=cmd.ts,
            commandId=cmd.id,
            type="state_patch",
            payload=patch.dict(),
        )

        state.apply_patch(patch.path, patch.value)
        await persist_event(event)
        await publish_state(patch.dict())
        return event

    # Policy: Change mode
    elif cmd.action.startswith("set_mode"):
        new_mode = cmd.payload.get("mode", "idle")
        patch = StatePatch(ts=cmd.ts, path="/mode", value=new_mode)
        event = Event(
            id=cmd.id,
            ts=cmd.ts,
            commandId=cmd.id,
            type="state_patch",
            payload=patch.dict(),
        )

        state.apply_patch(patch.path, patch.value)
        await persist_event(event)
        await publish_state(patch.dict())
        return event

    # Policy: Gesture update
    elif cmd.action.startswith("gesture_"):
        gesture = cmd.payload.get("gesture", "idle")
        patch = StatePatch(ts=cmd.ts, path="/last_gesture", value=gesture)
        event = Event(
            id=cmd.id,
            ts=cmd.ts,
            commandId=cmd.id,
            type="state_patch",
            payload=patch.dict(),
        )

        state.apply_patch(patch.path, patch.value)
        await persist_event(event)
        await publish_state(patch.dict())
        return event

    # Unknown command - reject
    else:
        event = Event(
            id=cmd.id,
            ts=cmd.ts,
            commandId=cmd.id,
            type="rejected",
            payload={"reason": "unknown_action", "action": cmd.action},
        )
        await persist_event(event)
        return event


async def persist_event(e: Event):
    """
    Persist an event to SQLite for audit trail and replay.
    """
    try:
        async with aiosqlite.connect("data/control_plane.db") as db:
            await db.execute(
                "INSERT INTO events VALUES (?,?,?,?,?)",
                (e.id, e.ts, e.commandId, e.type, json.dumps(e.payload)),
            )
            await db.commit()
    except Exception as ex:
        print(f"Error persisting event: {ex}")


async def save_snapshot():
    """
    Periodically save full state snapshot to SQLite.
    """
    try:
        async with aiosqlite.connect("data/control_plane.db") as db:
            await db.execute(
                "INSERT INTO snapshots (ts, state) VALUES (?,?)",
                (datetime.utcnow().isoformat(), json.dumps(state.to_dict())),
            )
            await db.commit()
    except Exception as ex:
        print(f"Error saving snapshot: {ex}")
