import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.todos import get_all_todos
from app.models.morning_report_dto import Todo
from app.util.storage import read_json, write_json

router = APIRouter()


class VoiceInterpretRequest(BaseModel):
    text: str


class VoiceInterpretResponse(BaseModel):
    intent: str
    confidence: float
    action: str
    parameters: dict


@router.post("/api/v1/voice/interpret", response_model=VoiceInterpretResponse)
async def interpret_voice(request: VoiceInterpretRequest):
    """
    Mock voice intent parser using regex patterns.
    Supports: switch to (ambient|morning), add todo (.*), else unknown.
    """
    text = request.text.lower().strip()

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
