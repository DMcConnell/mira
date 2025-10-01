"""Pytest configuration and fixtures."""

import os
import tempfile
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def temp_data_dir(monkeypatch):
    """Create a temporary directory for test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set DATA_DIR environment variable BEFORE importing storage
        monkeypatch.setenv("DATA_DIR", tmpdir)

        # Re-initialize storage with new directory
        from app.util import storage

        storage._ensure()

        yield tmpdir


@pytest.fixture
def sample_todo():
    """Sample todo data for testing."""
    return {"text": "Test todo item", "done": False}


@pytest.fixture
def sample_todos():
    """Sample list of todos for testing."""
    return [
        {"text": "Buy groceries", "done": False},
        {"text": "Walk the dog", "done": True},
        {"text": "Write tests", "done": False},
    ]
