import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Set

from app.workers.gesture import gesture_worker
from app.workers.voice import voice_worker
from app.services.bus import subscribe
from app.services.db import init_db
from app.models.core import Command
from app.core.arbiter import handle_command, save_snapshot
from app.core.state import state


# WebSocket clients registry
clients: Set[WebSocket] = set()


async def broadcast_to_clients(patch: dict):
    """
    Forward state patches from Redis to all connected WebSocket clients.
    """
    disconnected = set()
    for client in clients:
        try:
            await client.send_json(patch)
        except Exception as e:
            print(f"Error broadcasting to client: {e}")
            disconnected.add(client)

    # Clean up disconnected clients
    clients.difference_update(disconnected)


async def redis_subscriber():
    """
    Background task that subscribes to Redis and forwards to WebSocket clients.
    """
    await subscribe(broadcast_to_clients)


async def snapshot_saver():
    """
    Background task that periodically saves state snapshots.
    """
    while True:
        await asyncio.sleep(60)  # Save snapshot every minute
        await save_snapshot()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown lifecycle management.
    """
    # Startup
    print("🚀 Control Plane starting up...")

    # Initialize database
    await init_db()
    print("✅ Database initialized")

    # Start background workers
    asyncio.create_task(gesture_worker())
    asyncio.create_task(voice_worker())
    asyncio.create_task(redis_subscriber())
    asyncio.create_task(snapshot_saver())
    print("✅ Background workers started")

    yield

    # Shutdown
    print("🛑 Control Plane shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Mira Control Plane",
    description="Real-time command pipeline and event persistence layer",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "control-plane", "version": "2.0.0"}


@app.get("/state")
async def get_state():
    """
    Returns current in-memory state.
    Useful for initial sync when clients connect.
    """
    return state.to_dict()


@app.post("/command")
async def post_command(cmd: Command):
    """
    Accept a command and process it through the arbiter.
    Returns the resulting event.
    """
    event = await handle_command(cmd)
    return {"status": event.type, "payload": event.payload, "event_id": event.id}


@app.websocket("/ws/state")
async def ws_state(websocket: WebSocket):
    """
    WebSocket endpoint for real-time state updates.
    Clients connect here to receive StatePatch broadcasts.
    """
    await websocket.accept()
    clients.add(websocket)

    print(f"WebSocket client connected. Total clients: {len(clients)}")

    try:
        # Send initial state
        await websocket.send_json({"type": "initial_state", "data": state.to_dict()})

        # Keep connection alive and handle any incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                # Could handle client commands here if needed
                print(f"Received from client: {data}")
            except WebSocketDisconnect:
                break

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        clients.discard(websocket)
        print(f"WebSocket client disconnected. Total clients: {len(clients)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8090)
