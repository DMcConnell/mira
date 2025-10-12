"""
Vision WebSocket - Subscribe to Redis vision channel and forward to clients.
Receives real-time gesture detection data from gesture-worker.
"""

import asyncio
import json
import os
from typing import Set

import redis.asyncio as aioredis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
VISION_CHANNEL = "mira:vision"

# Store all connected WebSocket clients
vision_clients: Set[WebSocket] = set()


async def redis_vision_subscriber():
    """
    Background task that subscribes to Redis vision channel
    and forwards vision intents to all WebSocket clients.
    """
    while True:
        try:
            r = await aioredis.from_url(REDIS_URL, decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe(VISION_CHANNEL)

            print(f"[Vision WS] Subscribed to Redis channel: {VISION_CHANNEL}")

            async for msg in pubsub.listen():
                if msg["type"] == "message":
                    try:
                        data = json.loads(msg["data"])
                        # Broadcast to all connected clients
                        for client in list(vision_clients):
                            try:
                                await client.send_json(data)
                            except Exception as e:
                                print(f"[Vision WS] Error sending to client: {e}")
                                vision_clients.discard(client)
                    except json.JSONDecodeError as e:
                        print(f"[Vision WS] Error decoding message: {e}")
                    except Exception as e:
                        print(f"[Vision WS] Error processing message: {e}")

        except Exception as e:
            print(f"[Vision WS] Redis connection error: {e}")
            # Retry after delay
            await asyncio.sleep(5)


@router.websocket("/ws/vision")
async def vision_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time vision/gesture updates.
    Clients connect here to receive gesture detection data from the gesture-worker.
    """
    await websocket.accept()
    vision_clients.add(websocket)

    print(f"[Vision WS] Client connected. Total clients: {len(vision_clients)}")

    try:
        # Keep the connection alive and wait for disconnect
        while True:
            # We could receive messages from the client here if needed
            # For now, just wait for disconnect
            await websocket.receive_text()

    except WebSocketDisconnect:
        print(f"[Vision WS] Client disconnected")
    except Exception as e:
        print(f"[Vision WS] Error: {e}")
    finally:
        vision_clients.discard(websocket)
        print(f"[Vision WS] Client removed. Total clients: {len(vision_clients)}")
        try:
            await websocket.close()
        except Exception:
            pass
