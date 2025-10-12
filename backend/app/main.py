import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    auth,
    command,
    health,
    morning_report,
    settings,
    todos,
    vision,
    voice,
)
from app.ws import state as state_ws
from app.ws import vision as vision_ws

# Create FastAPI application
app = FastAPI(
    title="Mira Smart Mirror API",
    description="Backend API for the Mira smart mirror application",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, tags=["auth"])
app.include_router(command.router, tags=["command"])
app.include_router(health.router, tags=["health"])
app.include_router(morning_report.router, tags=["morning-report"])
app.include_router(todos.router, tags=["todos"])
app.include_router(voice.router, tags=["voice"])
app.include_router(settings.router, tags=["settings"])
app.include_router(vision.router, tags=["vision"])

# Include WebSocket routers
app.include_router(state_ws.router, tags=["websocket"])
app.include_router(vision_ws.router, tags=["websocket"])


@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup."""
    # Start Redis subscriber for state updates
    asyncio.create_task(state_ws.redis_subscriber())
    # Start Redis subscriber for vision updates
    asyncio.create_task(vision_ws.redis_vision_subscriber())


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Mira Smart Mirror API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
