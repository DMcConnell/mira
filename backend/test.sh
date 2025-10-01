#!/bin/bash
# Test runner script for Mira backend

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run tests based on argument
case "${1:-all}" in
    "all")
        echo "Running all tests..."
        pytest
        ;;
    "coverage")
        echo "Running tests with coverage..."
        pytest --cov=app --cov-report=html --cov-report=term
        echo "Coverage report generated in htmlcov/index.html"
        ;;
    "quick")
        echo "Running quick tests (no slow tests)..."
        pytest -m "not slow" -q
        ;;
    "verbose")
        echo "Running tests in verbose mode..."
        pytest -vv
        ;;
    "watch")
        echo "Running tests in watch mode..."
        pytest -f
        ;;
    *)
        echo "Usage: ./test.sh [all|coverage|quick|verbose|watch]"
        echo "  all      - Run all tests (default)"
        echo "  coverage - Run tests with coverage report"
        echo "  quick    - Run only fast tests"
        echo "  verbose  - Run with verbose output"
        echo "  watch    - Run in watch mode"
        exit 1
        ;;
esac
