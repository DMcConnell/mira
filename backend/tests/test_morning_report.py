"""Tests for morning report schema and endpoint."""

import pytest
from fastapi.testclient import TestClient


def test_morning_report_endpoint_exists(client: TestClient):
    """Test that the morning report endpoint exists."""
    response = client.get("/api/v1/morning-report")
    assert response.status_code == 200


def test_morning_report_schema(client: TestClient):
    """Test that morning report has correct schema."""
    response = client.get("/api/v1/morning-report")
    assert response.status_code == 200

    data = response.json()

    # Check top-level keys
    assert "calendar" in data
    assert "weather" in data
    assert "news" in data
    assert "todos" in data


def test_morning_report_calendar_structure(client: TestClient):
    """Test calendar items structure in morning report."""
    response = client.get("/api/v1/morning-report")
    data = response.json()

    calendar = data["calendar"]
    assert isinstance(calendar, list)

    # If there are calendar items, check structure
    if len(calendar) > 0:
        item = calendar[0]
        assert "id" in item
        assert "title" in item
        assert "startsAtISO" in item
        assert "endsAtISO" in item
        # location is optional


def test_morning_report_weather_structure(client: TestClient):
    """Test weather structure in morning report."""
    response = client.get("/api/v1/morning-report")
    data = response.json()

    weather = data["weather"]
    assert isinstance(weather, dict)
    assert "updatedISO" in weather
    assert "tempC" in weather
    assert "condition" in weather
    assert "icon" in weather
    assert "stale" in weather

    # Check types
    assert isinstance(weather["tempC"], (int, float))
    assert isinstance(weather["condition"], str)
    assert isinstance(weather["stale"], bool)


def test_morning_report_news_structure(client: TestClient):
    """Test news items structure in morning report."""
    response = client.get("/api/v1/morning-report")
    data = response.json()

    news = data["news"]
    assert isinstance(news, list)

    # If there are news items, check structure
    if len(news) > 0:
        item = news[0]
        assert "id" in item
        assert "title" in item
        assert "source" in item
        assert "url" in item
        assert "publishedISO" in item


def test_morning_report_todos_structure(client: TestClient, temp_data_dir):
    """Test todos structure in morning report."""
    response = client.get("/api/v1/morning-report")
    data = response.json()

    todos = data["todos"]
    assert isinstance(todos, list)


def test_morning_report_with_todos(client: TestClient, temp_data_dir):
    """Test that morning report includes created todos."""
    # Create a todo
    todo_data = {"text": "Test todo in morning report"}
    create_response = client.post("/api/v1/todos", json=todo_data)
    assert create_response.status_code == 200

    # Get morning report
    report_response = client.get("/api/v1/morning-report")
    assert report_response.status_code == 200

    data = report_response.json()
    todos = data["todos"]

    # Verify the todo appears in the report
    assert len(todos) > 0
    assert any(todo["text"] == "Test todo in morning report" for todo in todos)


def test_morning_report_weather_values(client: TestClient):
    """Test that weather returns reasonable mock values."""
    response = client.get("/api/v1/morning-report")
    data = response.json()

    weather = data["weather"]

    # Temperature should be in reasonable range (mock returns 20-25°C)
    assert 15 <= weather["tempC"] <= 30

    # Should have a condition
    assert len(weather["condition"]) > 0

    # Should have an icon
    assert len(weather["icon"]) > 0


def test_morning_report_news_count(client: TestClient):
    """Test that news returns expected number of items."""
    response = client.get("/api/v1/morning-report")
    data = response.json()

    news = data["news"]

    # Should return 5 news items (as per provider default)
    assert len(news) == 5


def test_morning_report_consistency(client: TestClient):
    """Test that multiple calls return consistent structure."""
    response1 = client.get("/api/v1/morning-report")
    response2 = client.get("/api/v1/morning-report")

    assert response1.status_code == 200
    assert response2.status_code == 200

    data1 = response1.json()
    data2 = response2.json()

    # Should have same keys
    assert data1.keys() == data2.keys()

    # Should have same structure
    assert isinstance(data1["calendar"], list)
    assert isinstance(data2["calendar"], list)
    assert isinstance(data1["weather"], dict)
    assert isinstance(data2["weather"], dict)
