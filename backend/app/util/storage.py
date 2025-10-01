import json
import os
import tempfile
from typing import Any

DATA_DIR = os.environ.get("DATA_DIR", "data")
TODO_FILE = os.path.join(DATA_DIR, "todos.json")


def _ensure():
    """Ensure data directory exists and create empty todos file if needed."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(TODO_FILE):
        with open(TODO_FILE, "w") as f:
            json.dump([], f)


# Initialize on module import
_ensure()


def read_json(path=TODO_FILE):
    """Read JSON data from file."""
    with open(path) as f:
        return json.load(f)


def write_json(obj: Any, path=TODO_FILE):
    """Write JSON data to file atomically using temporary file."""
    fd, tmp = tempfile.mkstemp(dir=DATA_DIR)
    with os.fdopen(fd, "w") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, path)


def get_todos_file_path() -> str:
    """Get the path to the todos JSON file."""
    return TODO_FILE


def get_data_dir() -> str:
    """Get the data directory path."""
    return DATA_DIR
