# Mira Smart Mirror

AI-powered smart mirror with gesture control, voice commands, and real-time information display.

## Quick Start

### Full Docker Stack (Mac/Development)

```bash
# Copy environment file
cp env.example .env

# Start all services
docker-compose up --build

# Open browser
open http://localhost
```

### Raspberry Pi Deployment

```bash
docker-compose up --build

# Run gesture-worker natively
cd gesture-worker
./run_native_pi.sh
```

See [gesture-worker/NATIVE_PI_SETUP.md](gesture-worker/NATIVE_PI_SETUP.md) for detailed instructions.

## Architecture

- **Backend**: FastAPI server with REST APIs and WebSocket support
- **Frontend**: React + TypeScript with real-time updates
- **Control Plane**: State management and command routing
- **Gesture Worker**: Hand gesture detection via MediaPipe
- **Redis**: Pub/sub messaging for real-time data

## Documentation

- [Gesture Worker Setup](gesture-worker/NATIVE_PI_SETUP.md) - Native Pi deployment
- [Project Roadmap](docs/project_mira_roadmap.md) - Feature roadmap

## Build Script Guide

```bash
# Build backend locally
./build.sh backend

# Build frontend locally
./build.sh frontend

# Build all services locally
./build.sh all

# Build and publish backend with version
./build.sh --publish v1.0.0 backend

# Build and publish all services with custom registry
./build.sh --publish v1.0.0 --registry myregistry.io all
```

## Development

### Backend

```bash
cd backend
pip install -r requirements.txt
./run.sh
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Control Plane

```bash
cd control-plane
pip install -r requirements.txt
./run.sh
```

### Gesture Worker (Mac)

```bash
cd gesture-worker
make setup
make run
```

## Environment Variables

See `env.example` for all configuration options. Key variables:

- `MIRA_ENV`: `mac` or `pi` - Controls camera initialization
- `REDIS_URL`: Redis connection URL
- `CONTROL_PLANE_URL`: Control Plane service URL
- `JWT_SECRET`: Secret for JWT authentication
- `MIRA_PIN`: PIN for authentication

## Contributing

1. Follow existing code style
2. Write tests for new features
3. Update documentation
4. Test on both Mac and Raspberry Pi if possible
