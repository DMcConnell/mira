from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, morning_report, settings, todos, voice

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
app.include_router(health.router, tags=["health"])
app.include_router(morning_report.router, tags=["morning-report"])
app.include_router(todos.router, tags=["todos"])
app.include_router(voice.router, tags=["voice"])
app.include_router(settings.router, tags=["settings"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Mira Smart Mirror API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
