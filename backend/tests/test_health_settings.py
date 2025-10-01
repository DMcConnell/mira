"""Tests for health and settings endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_endpoint_exists(self, client: TestClient):
        """Test that health endpoint exists."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_status(self, client: TestClient):
        """Test health check returns ok status."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "ok"

    def test_health_response_structure(self, client: TestClient):
        """Test health response has correct structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data

    def test_health_timestamp_format(self, client: TestClient):
        """Test health timestamp is valid ISO format."""
        from datetime import datetime

        response = client.get("/health")
        data = response.json()

        # Should be parseable as ISO datetime
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    def test_health_service_name(self, client: TestClient):
        """Test health returns correct service name."""
        response = client.get("/health")
        data = response.json()

        assert data["service"] == "mira-backend"


class TestSettingsEndpoint:
    """Tests for settings endpoints."""

    def test_get_settings_endpoint(self, client: TestClient):
        """Test getting settings."""
        response = client.get("/api/v1/settings")
        assert response.status_code == 200

    def test_get_settings_structure(self, client: TestClient):
        """Test settings response structure."""
        response = client.get("/api/v1/settings")
        data = response.json()

        assert "weatherMode" in data
        assert "newsMode" in data

    def test_get_settings_defaults(self, client: TestClient):
        """Test default settings values."""
        response = client.get("/api/v1/settings")
        data = response.json()

        # Default values should be "mock"
        assert data["weatherMode"] == "mock"
        assert data["newsMode"] == "mock"

    def test_update_settings(self, client: TestClient):
        """Test updating settings."""
        new_settings = {"weatherMode": "live", "newsMode": "live"}

        response = client.put("/api/v1/settings", json=new_settings)
        assert response.status_code == 200

        data = response.json()
        assert data["weatherMode"] == "live"
        assert data["newsMode"] == "live"

    def test_settings_persistence_in_memory(self, client: TestClient):
        """Test that settings persist in memory across requests."""
        # Update settings
        new_settings = {"weatherMode": "live", "newsMode": "mock"}

        update_response = client.put("/api/v1/settings", json=new_settings)
        assert update_response.status_code == 200

        # Get settings again
        get_response = client.get("/api/v1/settings")
        data = get_response.json()

        assert data["weatherMode"] == "live"
        assert data["newsMode"] == "mock"

    def test_update_partial_settings(self, client: TestClient):
        """Test updating only some settings fields."""
        # This tests that Pydantic model handles complete replacement
        new_settings = {"weatherMode": "custom", "newsMode": "custom"}

        response = client.put("/api/v1/settings", json=new_settings)
        assert response.status_code == 200


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint exists."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_response_structure(self, client: TestClient):
        """Test root response structure."""
        response = client.get("/")
        data = response.json()

        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data

    def test_root_docs_link(self, client: TestClient):
        """Test that root response includes docs link."""
        response = client.get("/")
        data = response.json()

        assert data["docs"] == "/docs"
        assert data["health"] == "/health"
