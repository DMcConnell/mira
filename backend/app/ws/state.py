"""
State WebSocket - Subscribe to Redis Pub/Sub and forward state patches to clients.
"""

import asyncio
import json
import os
from typing import Set

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CHANNEL = "mira:state"

# Store all connected WebSocket clients
clients: Set[WebSocket] = set()


async def redis_subscriber():
    """
    Background task that subscribes to Redis and forwards messages to all WebSocket clients.
    This runs once when the application starts.
    """
    while True:
        try:
            r = await aioredis.from_url(REDIS_URL, decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe(CHANNEL)

            print(f"[State WS] Subscribed to Redis channel: {CHANNEL}")

            async for msg in pubsub.listen():
                if msg["type"] == "message":
                    try:
                        data = json.loads(msg["data"])
                        # Broadcast to all connected clients
                        for client in list(clients):
                            try:
                                await client.send_json(data)
                            except Exception as e:
                                print(f"[State WS] Error sending to client: {e}")
                                clients.discard(client)
                    except json.JSONDecodeError as e:
                        print(f"[State WS] Error decoding message: {e}")
                    except Exception as e:
                        print(f"[State WS] Error processing message: {e}")

        except Exception as e:
            print(f"[State WS] Redis connection error: {e}")
            # Retry after delay
            await asyncio.sleep(5)


@router.websocket("/ws/state")
async def state_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time state updates.
    Clients connect here to receive state patches broadcast from the Control Plane.
    """
    await websocket.accept()
    clients.add(websocket)

    print(f"[State WS] Client connected. Total clients: {len(clients)}")

    try:
        # Keep the connection alive and wait for disconnect
        while True:
            # We could receive messages from the client here if needed
            # For now, just wait for disconnect
            await websocket.receive_text()

    except WebSocketDisconnect:
        print(f"[State WS] Client disconnected")
    except Exception as e:
        print(f"[State WS] Error: {e}")
    finally:
        clients.discard(websocket)
        print(f"[State WS] Client removed. Total clients: {len(clients)}")
        try:
            await websocket.close()
        except Exception:
            pass
