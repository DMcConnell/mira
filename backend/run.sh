#!/bin/bash
# Simple run script for the Mira backend server

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the server
uvicorn app.main:app --reload --port 8080 --host 0.0.0.0
