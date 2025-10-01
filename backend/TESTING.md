# Testing Guide - Mira Backend

Comprehensive testing guide for the Mira smart mirror backend.

## Test Suite Overview

The test suite includes:

- **Unit Tests**: Test individual functions and providers
- **Integration Tests**: Test API endpoints end-to-end
- **Schema Tests**: Validate response structures and data models

### Test Files

```
tests/
├── conftest.py              # Pytest fixtures and configuration
├── test_todos.py            # Todo CRUD operations (14 tests)
├── test_morning_report.py   # Morning report endpoint (11 tests)
├── test_providers.py        # Data providers (17 tests)
├── test_voice.py            # Voice intent parsing (15 tests)
└── test_health_settings.py  # Health and settings endpoints (13 tests)
```

**Total: 70+ tests**

## Running Tests

### Quick Start

```bash
# Run all tests
./test.sh

# Or use pytest directly
pytest
```

### Test Options

```bash
# Run with coverage report
./test.sh coverage

# Run only fast tests
./test.sh quick

# Run with verbose output
./test.sh verbose

# Run specific test file
pytest tests/test_todos.py

# Run specific test
pytest tests/test_todos.py::test_create_todo

# Run tests matching pattern
pytest -k "todo"
```

## Test Coverage

To generate a coverage report:

```bash
pytest --cov=app --cov-report=html --cov-report=term
```

View the HTML report:

```bash
open htmlcov/index.html
```

## Writing Tests

### Test Structure

Tests use `pytest` with FastAPI's `TestClient`:

```python
def test_example(client: TestClient):
    """Test description."""
    response = client.get("/api/v1/endpoint")
    assert response.status_code == 200
    assert response.json()["key"] == "expected_value"
```

### Using Fixtures

Common fixtures are available in `conftest.py`:

- `client`: FastAPI test client
- `temp_data_dir`: Temporary directory for test data
- `sample_todo`: Sample todo data
- `sample_todos`: List of sample todos

Example:

```python
def test_with_fixtures(client: TestClient, temp_data_dir, sample_todo):
    """Test using fixtures."""
    response = client.post("/api/v1/todos", json=sample_todo)
    assert response.status_code == 200
```

### Test Categories

Tests can be marked with categories:

```python
@pytest.mark.slow
def test_slow_operation(client):
    """This test takes a long time."""
    pass

@pytest.mark.integration
def test_full_workflow(client):
    """This tests multiple components together."""
    pass
```

Run specific categories:

```bash
pytest -m "not slow"        # Skip slow tests
pytest -m "integration"     # Only integration tests
```

## Test Coverage by Module

### Todos (`test_todos.py`)

- ✅ GET all todos (empty and with data)
- ✅ CREATE todo
- ✅ GET todo by ID
- ✅ UPDATE todo (text and done status)
- ✅ DELETE todo
- ✅ Error handling (404s)
- ✅ Data persistence
- ✅ Input validation

### Morning Report (`test_morning_report.py`)

- ✅ Endpoint existence
- ✅ Response schema validation
- ✅ Calendar items structure
- ✅ Weather data structure and values
- ✅ News items structure and count
- ✅ Todos integration
- ✅ Response consistency

### Providers (`test_providers.py`)

- ✅ Weather provider (snapshot, types, staleness)
- ✅ News provider (items, limits, staleness)
- ✅ Calendar provider (items, sorting, upcoming events)
- ✅ ISO timestamp validation
- ✅ Mock data generation

### Voice Commands (`test_voice.py`)

- ✅ Mode switching (ambient/morning)
- ✅ Add todo command
- ✅ Complete todo command
- ✅ Unknown commands
- ✅ Case insensitive parsing
- ✅ Whitespace handling
- ✅ Todo creation integration
- ✅ Response structure validation

### Health & Settings (`test_health_settings.py`)

- ✅ Health check endpoint
- ✅ Health response structure
- ✅ Settings GET/PUT
- ✅ Settings persistence
- ✅ Root endpoint

## Continuous Integration

### CI/CD Integration

Add to your CI pipeline:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Debugging Tests

### Run with verbose output

```bash
pytest -vv
```

### Show print statements

```bash
pytest -s
```

### Stop on first failure

```bash
pytest -x
```

### Drop into debugger on failure

```bash
pytest --pdb
```

### Run last failed tests

```bash
pytest --lf
```

## Test Data

Tests use temporary directories for data isolation. Each test that needs file persistence uses the `temp_data_dir` fixture, ensuring:

- No test data pollution
- Clean state for each test
- Parallel test execution safety

## Best Practices

1. **Isolation**: Each test should be independent
2. **Descriptive names**: Use clear, descriptive test names
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Fast tests**: Keep tests fast; mark slow tests
5. **Mock external services**: Don't hit real APIs in tests
6. **Coverage**: Aim for >80% code coverage
7. **Edge cases**: Test both happy path and error cases

## Troubleshooting

### Tests failing with import errors

```bash
# Make sure you're in the right directory
cd /path/to/backend

# Ensure dependencies are installed
pip install -r requirements.txt
```

### Data persistence issues

The `temp_data_dir` fixture should handle cleanup automatically. If you see stale data, check that you're using the fixture properly.

### Port conflicts

Tests use `TestClient` which doesn't bind to actual ports, so port conflicts shouldn't occur.

## Next Steps

- [ ] Add WebSocket tests
- [ ] Add performance/load tests
- [ ] Add security tests
- [ ] Increase coverage to >90%
- [ ] Add mutation testing
- [ ] Add API contract tests
