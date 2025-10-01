# Mira Smart Mirror - Backend

FastAPI backend server for the Mira smart mirror application.

## Features

- **Morning Report API**: Aggregates calendar, weather, news, and todos
- **Todo Management**: Full CRUD operations with file persistence
- **Voice Commands**: Mock intent parser for voice interactions
- **Settings Management**: In-memory settings storage
- **Vision/AI Mocks**: Static snapshot image and WebSocket for gesture intents
- **Health Check**: Server status endpoint

## Setup

### 1. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Server

```bash
uvicorn app.main:app --reload --port 8080
```

Or use the provided run script:

```bash
./run.sh
```

## API Endpoints

### Core Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check
- `GET /docs` - OpenAPI documentation (Swagger UI)

### Morning Report

- `GET /api/v1/morning-report` - Get aggregated morning report data

### Todos

- `GET /api/v1/todos` - List all todos
- `POST /api/v1/todos` - Create a new todo
- `GET /api/v1/todos/{id}` - Get specific todo
- `PUT /api/v1/todos/{id}` - Update todo
- `DELETE /api/v1/todos/{id}` - Delete todo

### Voice Commands

- `POST /api/v1/voice/interpret` - Parse voice command text

Supported commands:

- `"switch to ambient"` - Switch to ambient mode
- `"switch to morning"` - Switch to morning mode
- `"add todo <text>"` - Create a new todo item

### Settings

- `GET /api/v1/settings` - Get current settings
- `PUT /api/v1/settings` - Update settings

### Vision (Mock)

- `GET /vision/snapshot.jpg` - Get static snapshot image
- `WS /ws/vision` - WebSocket for mock vision intents

## Data Persistence

Todos are persisted to `data/todos.json` and will survive server restarts.

## Testing

Access the interactive API documentation at:

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

### Manual Tests

```bash
# Health check
curl http://localhost:8080/health

# Get morning report
curl http://localhost:8080/api/v1/morning-report

# Create a todo
curl -X POST http://localhost:8080/api/v1/todos \
  -H "Content-Type: application/json" \
  -d '{"text": "Buy milk"}'

# Voice command
curl -X POST http://localhost:8080/api/v1/voice/interpret \
  -H "Content-Type: application/json" \
  -d '{"text": "add todo buy milk"}'
```

## Testing

Run the test suite to verify everything works:

```bash
# Run all tests
./test.sh

# Run with coverage
./test.sh coverage

# Run specific test file
pytest tests/test_todos.py
```

The test suite includes 70+ tests covering:

- Todo CRUD operations
- Morning report schema validation
- Provider functions
- Voice intent parsing
- Health and settings endpoints

See [TESTING.md](TESTING.md) for detailed testing documentation.

## Project Structure

```
backend/
├── app/
│   ├── api/           # API endpoints
│   │   ├── health.py
│   │   ├── morning_report.py
│   │   ├── settings.py
│   │   ├── todos.py
│   │   ├── vision.py
│   │   └── voice.py
│   ├── models/        # Pydantic models
│   │   ├── app_wide.py
│   │   └── morning_report.py
│   ├── providers/     # Data providers
│   │   ├── calendar.py
│   │   ├── news.py
│   │   └── weather.py
│   ├── util/          # Utilities
│   │   └── storage.py
│   ├── ws/            # WebSocket endpoints
│   │   └── vision.py
│   ├── static/        # Static files
│   │   └── sample.jpg
│   └── main.py        # FastAPI application
├── data/              # Persistent data
│   └── todos.json
├── tests/             # Test suite (70+ tests)
│   ├── conftest.py
│   ├── test_todos.py
│   ├── test_morning_report.py
│   ├── test_providers.py
│   ├── test_voice.py
│   └── test_health_settings.py
├── requirements.txt
├── pytest.ini
├── run.sh
├── test.sh
├── README.md
└── TESTING.md
```

## Environment Variables

- `DATA_DIR` - Directory for persistent data (default: `data`)

## Development

The server runs in development mode with auto-reload enabled. Any code changes will automatically restart the server.

## Next Steps

- [ ] Implement unit tests (see `tests/` directory)
- [ ] Replace mock providers with real API integrations
- [ ] Add authentication/authorization
- [ ] Implement WebSocket authentication
- [ ] Add logging and monitoring
- [ ] Create Docker container (see phase_1_detailed.md Guide 3)
