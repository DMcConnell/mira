from ..models.core import Command, Event, StatePatch
from ..services.bus import publish_state
from .state import state
import json
import aiosqlite
from datetime import datetime

# App registry (matches frontend)
APP_REGISTRY = [
    "home",
    "weather",
    "email",  # Private only
    "finance",  # Private only
    "news",
    "todos",
    "calendar",
    "settings",  # Always visible
]


def _get_visible_apps(mode: str) -> list:
    """Get visible apps based on privacy mode"""
    if mode == "public":
        return [app for app in APP_REGISTRY if app not in ["email", "finance"]]
    return APP_REGISTRY


def _is_app_visible(app_id: str, mode: str) -> bool:
    """Check if app is visible in current mode"""
    return app_id in _get_visible_apps(mode)


def _get_next_app(current_app: str, mode: str) -> str:
    """Get next app in registry"""
    visible_apps = _get_visible_apps(mode)
    try:
        current_idx = visible_apps.index(current_app)
        next_idx = (current_idx + 1) % len(visible_apps)
        return visible_apps[next_idx]
    except ValueError:
        # Current app not in visible list, return first
        return visible_apps[0] if visible_apps else "home"


def _get_prev_app(current_app: str, mode: str) -> str:
    """Get previous app in registry"""
    visible_apps = _get_visible_apps(mode)
    try:
        current_idx = visible_apps.index(current_app)
        prev_idx = (current_idx - 1) % len(visible_apps)
        return visible_apps[prev_idx]
    except ValueError:
        # Current app not in visible list, return last
        return visible_apps[-1] if visible_apps else "home"


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

    # Policy: Set GN armed state
    elif cmd.action == "set_gn_armed":
        gn_armed = cmd.payload.get("gnArmed", False)
        patch = StatePatch(ts=cmd.ts, path="/ui/gnArmed", value=gn_armed)
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

    # Policy: Global Navigation (GN) commands
    elif cmd.action == "nav.nextApp":
        # Navigate to next app in registry
        app_route = _get_next_app(state.app_route, state.ui_mode)
        patch = StatePatch(ts=cmd.ts, path="/ui/appRoute", value=app_route)
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

    elif cmd.action == "nav.prevApp":
        # Navigate to previous app in registry
        app_route = _get_prev_app(state.app_route, state.ui_mode)
        patch = StatePatch(ts=cmd.ts, path="/ui/appRoute", value=app_route)
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

    elif cmd.action == "nav.openAppFocused":
        # Open the currently focused app (if in app rail)
        # For now, just confirm current app
        patch = StatePatch(ts=cmd.ts, path="/ui/focusPath", value=[])
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

    elif cmd.action == "nav.backOrHome":
        # Navigate back or to home
        if state.app_route != "home":
            patch = StatePatch(ts=cmd.ts, path="/ui/appRoute", value="home")
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

    # Policy: In-App Navigation (IAN) commands
    elif cmd.action == "app.navigate":
        direction = cmd.payload.get("direction", "next")
        # App-specific navigation will be handled by frontend
        # Just acknowledge the command
        event = Event(
            id=cmd.id,
            ts=cmd.ts,
            commandId=cmd.id,
            type="accepted",
            payload={"action": cmd.action, "direction": direction},
        )
        await persist_event(event)
        return event

    elif cmd.action == "app.selectFocus":
        # App-specific focus selection will be handled by frontend
        event = Event(
            id=cmd.id,
            ts=cmd.ts,
            commandId=cmd.id,
            type="accepted",
            payload={"action": cmd.action},
        )
        await persist_event(event)
        return event

    elif cmd.action == "app.quickActions":
        # App-specific quick actions will be handled by frontend
        event = Event(
            id=cmd.id,
            ts=cmd.ts,
            commandId=cmd.id,
            type="accepted",
            payload={"action": cmd.action},
        )
        await persist_event(event)
        return event

    # Policy: Voice commands
    elif cmd.action == "voice.openApp":
        app_id = cmd.payload.get("app")
        if app_id and _is_app_visible(app_id, state.ui_mode):
            patch = StatePatch(ts=cmd.ts, path="/ui/appRoute", value=app_id)
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

    elif cmd.action == "voice.nav":
        nav_action = cmd.payload.get("action")
        # Translate voice nav to appropriate command
        if nav_action == "next":
            # Context-aware: GN if in app rail context, else IAN
            return await handle_command(
                Command(
                    id=cmd.id,
                    ts=cmd.ts,
                    source="voice",
                    action="nav.nextApp",
                    payload={},
                )
            )
        elif nav_action == "prev" or nav_action == "previous":
            return await handle_command(
                Command(
                    id=cmd.id,
                    ts=cmd.ts,
                    source="voice",
                    action="nav.prevApp",
                    payload={},
                )
            )
        elif nav_action == "back":
            return await handle_command(
                Command(
                    id=cmd.id,
                    ts=cmd.ts,
                    source="voice",
                    action="nav.backOrHome",
                    payload={},
                )
            )
        elif nav_action == "select":
            return await handle_command(
                Command(
                    id=cmd.id,
                    ts=cmd.ts,
                    source="voice",
                    action="app.selectFocus",
                    payload={},
                )
            )

    # Policy: System commands
    elif cmd.action == "system.toggleDebug":
        new_state = not state.debug_enabled
        patch = StatePatch(ts=cmd.ts, path="/ui/debug/enabled", value=new_state)
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

    elif cmd.action == "system.setMode":
        new_mode = cmd.payload.get("mode")
        code = cmd.payload.get("code")
        private_code = "unlock"  # Should be from env/config

        if new_mode == "private":
            # Require code
            if code != private_code:
                event = Event(
                    id=cmd.id,
                    ts=cmd.ts,
                    commandId=cmd.id,
                    type="rejected",
                    payload={"reason": "invalid_code", "action": cmd.action},
                )
                await persist_event(event)
                return event

        # Check if switching from private to public while in private app
        if state.ui_mode == "private" and new_mode == "public":
            if state.app_route in ["email", "finance"]:
                # Navigate to home first
                state.app_route = "home"
                patch1 = StatePatch(ts=cmd.ts, path="/ui/appRoute", value="home")
                await publish_state(patch1.dict())

        patch = StatePatch(ts=cmd.ts, path="/ui/mode", value=new_mode)
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
