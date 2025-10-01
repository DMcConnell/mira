import json
import os
import tempfile
from typing import Any


def get_data_dir() -> str:
    """Get the data directory path (dynamic based on environment)."""
    return os.environ.get("DATA_DIR", "data")


def get_todos_file_path() -> str:
    """Get the path to the todos JSON file (dynamic based on environment)."""
    return os.path.join(get_data_dir(), "todos.json")


def _ensure():
    """Ensure data directory exists and create empty todos file if needed."""
    data_dir = get_data_dir()
    todo_file = get_todos_file_path()

    os.makedirs(data_dir, exist_ok=True)
    if not os.path.exists(todo_file):
        with open(todo_file, "w") as f:
            json.dump([], f)


# Initialize on module import
_ensure()


def read_json(path=None):
    """Read JSON data from file."""
    if path is None:
        path = get_todos_file_path()
    with open(path) as f:
        return json.load(f)


def write_json(obj: Any, path=None):
    """Write JSON data to file atomically using temporary file."""
    if path is None:
        path = get_todos_file_path()

    data_dir = get_data_dir()
    fd, tmp = tempfile.mkstemp(dir=data_dir)
    with os.fdopen(fd, "w") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, path)
