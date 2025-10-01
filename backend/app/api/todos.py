import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.morning_report_dto import Todo
from app.util.storage import read_json, write_json

router = APIRouter()


class CreateTodoRequest(BaseModel):
    text: str


class UpdateTodoRequest(BaseModel):
    text: Optional[str] = None
    done: Optional[bool] = None


@router.get("/api/v1/todos", response_model=List[Todo])
async def get_todos():
    """Get all todos."""
    try:
        todos_data = read_json()
        return [Todo(**todo) for todo in todos_data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read todos: {str(e)}")


@router.post("/api/v1/todos", response_model=Todo)
async def create_todo(request: CreateTodoRequest):
    """Create a new todo."""
    try:
        todos_data = read_json()

        new_todo = Todo(
            id=str(uuid.uuid4()),
            text=request.text,
            done=False,
            createdAtISO=datetime.now(timezone.utc).isoformat(),
        )

        todos_data.append(new_todo.dict())
        write_json(todos_data)

        return new_todo
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create todo: {str(e)}")


@router.get("/api/v1/todos/{todo_id}", response_model=Todo)
async def get_todo(todo_id: str):
    """Get a specific todo by ID."""
    try:
        todos_data = read_json()
        for todo in todos_data:
            if todo["id"] == todo_id:
                return Todo(**todo)

        raise HTTPException(status_code=404, detail="Todo not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get todo: {str(e)}")


@router.put("/api/v1/todos/{todo_id}", response_model=Todo)
async def update_todo(todo_id: str, request: UpdateTodoRequest):
    """Update a specific todo by ID."""
    try:
        todos_data = read_json()

        for i, todo in enumerate(todos_data):
            if todo["id"] == todo_id:
                # Update fields if provided
                if request.text is not None:
                    todo["text"] = request.text
                if request.done is not None:
                    todo["done"] = request.done

                todos_data[i] = todo
                write_json(todos_data)

                return Todo(**todo)

        raise HTTPException(status_code=404, detail="Todo not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update todo: {str(e)}")


@router.delete("/api/v1/todos/{todo_id}")
async def delete_todo(todo_id: str):
    """Delete a specific todo by ID."""
    try:
        todos_data = read_json()

        for i, todo in enumerate(todos_data):
            if todo["id"] == todo_id:
                del todos_data[i]
                write_json(todos_data)
                return {"message": "Todo deleted successfully"}

        raise HTTPException(status_code=404, detail="Todo not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete todo: {str(e)}")


def get_all_todos() -> List[Todo]:
    """Helper function to get all todos for use by other modules."""
    try:
        todos_data = read_json()
        return [Todo(**todo) for todo in todos_data]
    except Exception:
        # Return empty list if there's an error reading todos
        return []
