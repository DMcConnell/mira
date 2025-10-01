"""Tests for todos CRUD operations."""

import pytest
from fastapi.testclient import TestClient


def test_get_todos_empty(client: TestClient, temp_data_dir):
    """Test getting todos when none exist."""
    response = client.get("/api/v1/todos")
    assert response.status_code == 200
    assert response.json() == []


def test_create_todo(client: TestClient, temp_data_dir, sample_todo):
    """Test creating a new todo."""
    response = client.post("/api/v1/todos", json=sample_todo)
    assert response.status_code == 200

    data = response.json()
    assert data["text"] == sample_todo["text"]
    assert data["done"] == sample_todo["done"]
    assert "id" in data
    assert "createdAtISO" in data


def test_get_todos_after_create(client: TestClient, temp_data_dir, sample_todo):
    """Test getting todos after creating some."""
    # Create a todo
    create_response = client.post("/api/v1/todos", json=sample_todo)
    assert create_response.status_code == 200

    # Get all todos
    get_response = client.get("/api/v1/todos")
    assert get_response.status_code == 200

    todos = get_response.json()
    assert len(todos) == 1
    assert todos[0]["text"] == sample_todo["text"]


def test_get_todo_by_id(client: TestClient, temp_data_dir, sample_todo):
    """Test getting a specific todo by ID."""
    # Create a todo
    create_response = client.post("/api/v1/todos", json=sample_todo)
    todo_id = create_response.json()["id"]

    # Get the todo by ID
    response = client.get(f"/api/v1/todos/{todo_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == todo_id
    assert data["text"] == sample_todo["text"]


def test_get_todo_not_found(client: TestClient, temp_data_dir):
    """Test getting a non-existent todo."""
    response = client.get("/api/v1/todos/nonexistent-id")
    assert response.status_code == 404


def test_update_todo_text(client: TestClient, temp_data_dir, sample_todo):
    """Test updating todo text."""
    # Create a todo
    create_response = client.post("/api/v1/todos", json=sample_todo)
    todo_id = create_response.json()["id"]

    # Update the todo
    update_data = {"text": "Updated todo text"}
    response = client.put(f"/api/v1/todos/{todo_id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["text"] == "Updated todo text"
    assert data["done"] == sample_todo["done"]  # Should remain unchanged


def test_update_todo_done_status(client: TestClient, temp_data_dir, sample_todo):
    """Test updating todo done status."""
    # Create a todo
    create_response = client.post("/api/v1/todos", json=sample_todo)
    todo_id = create_response.json()["id"]

    # Update the done status
    update_data = {"done": True}
    response = client.put(f"/api/v1/todos/{todo_id}", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["done"] is True
    assert data["text"] == sample_todo["text"]  # Should remain unchanged


def test_update_todo_not_found(client: TestClient, temp_data_dir):
    """Test updating a non-existent todo."""
    update_data = {"text": "Should fail"}
    response = client.put("/api/v1/todos/nonexistent-id", json=update_data)
    assert response.status_code == 404


def test_delete_todo(client: TestClient, temp_data_dir, sample_todo):
    """Test deleting a todo."""
    # Create a todo
    create_response = client.post("/api/v1/todos", json=sample_todo)
    todo_id = create_response.json()["id"]

    # Delete the todo
    response = client.delete(f"/api/v1/todos/{todo_id}")
    assert response.status_code == 200
    assert "message" in response.json()

    # Verify it's deleted
    get_response = client.get(f"/api/v1/todos/{todo_id}")
    assert get_response.status_code == 404


def test_delete_todo_not_found(client: TestClient, temp_data_dir):
    """Test deleting a non-existent todo."""
    response = client.delete("/api/v1/todos/nonexistent-id")
    assert response.status_code == 404


def test_todos_persistence(client: TestClient, temp_data_dir, sample_todos):
    """Test that todos persist across requests."""
    # Create multiple todos
    created_ids = []
    for todo in sample_todos:
        response = client.post("/api/v1/todos", json=todo)
        assert response.status_code == 200
        created_ids.append(response.json()["id"])

    # Get all todos
    response = client.get("/api/v1/todos")
    assert response.status_code == 200

    todos = response.json()
    assert len(todos) == len(sample_todos)

    # Verify all todos are present
    for i, todo in enumerate(todos):
        assert todo["id"] in created_ids
        assert todo["text"] in [t["text"] for t in sample_todos]


def test_create_todo_validation(client: TestClient, temp_data_dir):
    """Test todo creation with invalid data."""
    # Missing required field
    response = client.post("/api/v1/todos", json={})
    assert response.status_code == 422  # Validation error
