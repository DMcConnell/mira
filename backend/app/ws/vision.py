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
    r = None
    pubsub = None

    while True:
        try:
            # Close existing connection if reconnecting
            if pubsub:
                try:
                    # Break out of listen() loop by closing the connection
                    # This will cause the async for loop to exit
                    await pubsub.unsubscribe(VISION_CHANNEL)
                except Exception:
                    pass
                pubsub = None
            if r:
                try:
                    await r.close()
                except Exception:
                    pass
                r = None

            # Create new connection
            r = await aioredis.from_url(REDIS_URL, decode_responses=True)
            pubsub = r.pubsub()
            await pubsub.subscribe(VISION_CHANNEL)

            print(f"[Vision WS] Subscribed to Redis channel: {VISION_CHANNEL}")

            try:
                async for msg in pubsub.listen():
                    # Skip subscribe confirmation messages
                    if msg["type"] == "subscribe":
                        continue

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
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"[Vision WS] Error in listen loop: {e}")
                # Break out of the loop to reconnect
                break

        except asyncio.CancelledError:
            # Clean shutdown
            print("[Vision WS] Shutting down...")
            if pubsub:
                try:
                    await pubsub.unsubscribe(VISION_CHANNEL)
                    await pubsub.close()
                except Exception:
                    pass
            if r:
                try:
                    await r.close()
                except Exception:
                    pass
            raise
        except Exception as e:
            print(f"[Vision WS] Redis connection error: {e}")
            # Clean up on error
            if pubsub:
                try:
                    await pubsub.unsubscribe(VISION_CHANNEL)
                    await pubsub.close()
                except Exception:
                    pass
                pubsub = None
            if r:
                try:
                    await r.close()
                except Exception:
                    pass
                r = None
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
