import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.todos import get_all_todos
from app.models.morning_report import Todo
from app.util.storage import read_json, write_json
from app.util.auth import require_capability, TokenData

router = APIRouter()


class VoiceInterpretRequest(BaseModel):
    text: str


class VoiceInterpretResponse(BaseModel):
    intent: str
    confidence: float
    action: str
    parameters: dict


@router.post("/api/v1/voice/interpret", response_model=VoiceInterpretResponse)
async def interpret_voice(
    request: VoiceInterpretRequest,
    token: TokenData = Depends(require_capability("command.send")),
):
    """
    Voice intent parser using regex patterns.
    Supports Phase A & B commands:
    - App switching: "open weather / email / finance / news / todos / calendar / settings / home"
    - Navigation: "next", "previous", "back", "select", "read that", "details"
    - System: "Mira enable debug overlay", "Mira disable debug", "Mira private mode <code>", "Mira public mode"
    - Legacy: switch to (ambient|morning), add todo, complete todo
    Requires 'command.send' capability.
    """
    text = request.text.lower().strip()

    # Pattern: Mira wake phrase (case-insensitive word boundary)
    wake_pattern = r"\bmira\b"
    has_wake = re.search(wake_pattern, text, re.IGNORECASE) is not None

    # System commands (require "Mira" wake phrase)
    if has_wake:
        # Debug overlay toggle
        if re.search(r"enable.*debug|debug.*on", text):
            return VoiceInterpretResponse(
                intent="system.toggleDebug",
                confidence=0.95,
                action="system.toggleDebug",
                parameters={"enable": True},
            )
        if re.search(r"disable.*debug|debug.*off", text):
            return VoiceInterpretResponse(
                intent="system.toggleDebug",
                confidence=0.95,
                action="system.toggleDebug",
                parameters={"enable": False},
            )

        # Privacy mode switching
        private_pattern = r"private mode\s+(\w+)"
        private_match = re.search(private_pattern, text)
        if private_match:
            code = private_match.group(1).strip()
            return VoiceInterpretResponse(
                intent="system.setMode",
                confidence=0.90,
                action="system.setMode",
                parameters={"mode": "private", "code": code},
            )

        if re.search(r"public mode", text):
            return VoiceInterpretResponse(
                intent="system.setMode",
                confidence=0.90,
                action="system.setMode",
                parameters={"mode": "public"},
            )

    # App opening commands
    app_patterns = {
        r"\bopen\s+(?:the\s+)?(?:home|dashboard)\b": "home",
        r"\bopen\s+(?:the\s+)?weather\b": "weather",
        r"\bopen\s+(?:the\s+)?email\b": "email",
        r"\bopen\s+(?:the\s+)?mail\b": "email",
        r"\bopen\s+(?:the\s+)?finance\b": "finance",
        r"\bopen\s+(?:the\s+)?news\b": "news",
        r"\bopen\s+(?:the\s+)?todos?\b": "todos",
        r"\bopen\s+(?:the\s+)?calendar\b": "calendar",
        r"\bopen\s+(?:the\s+)?settings\b": "settings",
    }

    for pattern, app_id in app_patterns.items():
        if re.search(pattern, text):
            return VoiceInterpretResponse(
                intent="voice.openApp",
                confidence=0.90,
                action="voice.openApp",
                parameters={"app": app_id},
            )

    # Navigation commands
    if re.search(r"\bnext\b", text):
        return VoiceInterpretResponse(
            intent="voice.nav",
            confidence=0.85,
            action="voice.nav",
            parameters={"action": "next"},
        )

    if re.search(r"\b(?:prev|previous)\b", text):
        return VoiceInterpretResponse(
            intent="voice.nav",
            confidence=0.85,
            action="voice.nav",
            parameters={"action": "prev"},
        )

    if re.search(r"\bback\b", text):
        return VoiceInterpretResponse(
            intent="voice.nav",
            confidence=0.85,
            action="voice.nav",
            parameters={"action": "back"},
        )

    if re.search(r"\bselect\b", text):
        return VoiceInterpretResponse(
            intent="voice.nav",
            confidence=0.85,
            action="voice.nav",
            parameters={"action": "select"},
        )

    if re.search(r"\bread\s+that\b", text):
        return VoiceInterpretResponse(
            intent="app.readAloud",
            confidence=0.85,
            action="app.readAloud",
            parameters={},
        )

    if re.search(r"\bdetails\b", text):
        return VoiceInterpretResponse(
            intent="app.details",
            confidence=0.85,
            action="app.details",
            parameters={},
        )

    # Legacy patterns (kept for backward compatibility)
    # Pattern: switch to ambient/morning
    mode_pattern = r"switch to (ambient|morning)"
    mode_match = re.search(mode_pattern, text)
    if mode_match:
        mode = mode_match.group(1)
        return VoiceInterpretResponse(
            intent="switch_mode",
            confidence=0.95,
            action=f"switch_to_{mode}",
            parameters={"mode": mode},
        )

    # Pattern: add todo
    todo_pattern = r"add todo (.+)"
    todo_match = re.search(todo_pattern, text)
    if todo_match:
        todo_text = todo_match.group(1).strip()

        # Actually create the todo
        try:
            todos_data = read_json()
            new_todo = Todo(
                id=str(uuid.uuid4()),
                text=todo_text,
                done=False,
                createdAtISO=datetime.now(timezone.utc).isoformat(),
            )
            todos_data.append(new_todo.dict())
            write_json(todos_data)

            return VoiceInterpretResponse(
                intent="add_todo",
                confidence=0.90,
                action="todo_created",
                parameters={"text": todo_text, "id": new_todo.id},
            )
        except Exception as e:
            return VoiceInterpretResponse(
                intent="add_todo",
                confidence=0.90,
                action="error",
                parameters={"text": todo_text, "error": str(e)},
            )

    # Pattern: complete/mark todo
    complete_pattern = r"(complete|mark|finish|done) todo (.+)"
    complete_match = re.search(complete_pattern, text)
    if complete_match:
        todo_identifier = complete_match.group(2).strip()
        return VoiceInterpretResponse(
            intent="complete_todo",
            confidence=0.85,
            action="todo_completed",
            parameters={"identifier": todo_identifier},
        )

    # Unknown intent
    return VoiceInterpretResponse(
        intent="unknown",
        confidence=0.0,
        action="no_action",
        parameters={"original_text": text},
    )
