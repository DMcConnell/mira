"""Tests for voice intent parsing."""

import pytest
from fastapi.testclient import TestClient


class TestVoiceInterpret:
    """Tests for voice interpretation endpoint."""

    def test_voice_endpoint_exists(self, client: TestClient):
        """Test that voice interpret endpoint exists."""
        response = client.post("/api/v1/voice/interpret", json={"text": "test"})
        assert response.status_code == 200

    def test_switch_to_ambient(self, client: TestClient):
        """Test switching to ambient mode."""
        response = client.post(
            "/api/v1/voice/interpret", json={"text": "switch to ambient"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["intent"] == "switch_mode"
        assert data["action"] == "switch_to_ambient"
        assert data["parameters"]["mode"] == "ambient"
        assert data["confidence"] > 0.9

    def test_switch_to_morning(self, client: TestClient):
        """Test switching to morning mode."""
        response = client.post(
            "/api/v1/voice/interpret", json={"text": "switch to morning"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["intent"] == "switch_mode"
        assert data["action"] == "switch_to_morning"
        assert data["parameters"]["mode"] == "morning"
        assert data["confidence"] > 0.9

    def test_add_todo_command(self, client: TestClient, temp_data_dir):
        """Test adding a todo via voice command."""
        response = client.post(
            "/api/v1/voice/interpret", json={"text": "add todo buy groceries"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["intent"] == "add_todo"
        assert data["action"] == "todo_created"
        assert data["parameters"]["text"] == "buy groceries"
        assert "id" in data["parameters"]
        assert data["confidence"] > 0.8

    def test_add_todo_creates_actual_todo(self, client: TestClient, temp_data_dir):
        """Test that voice command actually creates a todo."""
        # Add todo via voice
        voice_response = client.post(
            "/api/v1/voice/interpret", json={"text": "add todo test voice todo"}
        )
        assert voice_response.status_code == 200

        todo_id = voice_response.json()["parameters"]["id"]

        # Verify todo exists
        get_response = client.get(f"/api/v1/todos/{todo_id}")
        assert get_response.status_code == 200

        todo = get_response.json()
        assert todo["text"] == "test voice todo"
        assert todo["done"] is False

    def test_complete_todo_command(self, client: TestClient):
        """Test complete todo voice command."""
        response = client.post(
            "/api/v1/voice/interpret", json={"text": "complete todo buy milk"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["intent"] == "complete_todo"
        assert data["action"] == "todo_completed"
        assert data["parameters"]["identifier"] == "buy milk"

    def test_mark_todo_command(self, client: TestClient):
        """Test mark todo voice command."""
        response = client.post(
            "/api/v1/voice/interpret", json={"text": "mark todo buy milk"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["intent"] == "complete_todo"

    def test_unknown_command(self, client: TestClient):
        """Test unknown voice command."""
        response = client.post(
            "/api/v1/voice/interpret", json={"text": "do something random"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["intent"] == "unknown"
        assert data["action"] == "no_action"
        assert data["confidence"] == 0.0
        assert "original_text" in data["parameters"]

    def test_case_insensitive_parsing(self, client: TestClient):
        """Test that voice commands are case insensitive."""
        response = client.post(
            "/api/v1/voice/interpret", json={"text": "SWITCH TO AMBIENT"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["intent"] == "switch_mode"
        assert data["parameters"]["mode"] == "ambient"

    def test_voice_command_with_extra_whitespace(self, client: TestClient):
        """Test voice command with extra whitespace."""
        response = client.post(
            "/api/v1/voice/interpret", json={"text": "  switch to morning  "}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["intent"] == "switch_mode"

    def test_voice_response_structure(self, client: TestClient):
        """Test that voice response has correct structure."""
        response = client.post("/api/v1/voice/interpret", json={"text": "test"})

        assert response.status_code == 200
        data = response.json()

        # Check all required fields
        assert "intent" in data
        assert "confidence" in data
        assert "action" in data
        assert "parameters" in data

        # Check types
        assert isinstance(data["intent"], str)
        assert isinstance(data["confidence"], (int, float))
        assert isinstance(data["action"], str)
        assert isinstance(data["parameters"], dict)

    def test_voice_validation_error(self, client: TestClient):
        """Test voice endpoint with invalid request."""
        response = client.post(
            "/api/v1/voice/interpret", json={}  # Missing required 'text' field
        )

        assert response.status_code == 422  # Validation error
