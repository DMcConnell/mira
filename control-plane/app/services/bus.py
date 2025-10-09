import redis.asyncio as aioredis
import json
import asyncio
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CHANNEL = "mira:state"


async def publish_state(patch: dict):
    """
    Publish a state patch to Redis for broadcast to all subscribers.
    """
    try:
        r = await aioredis.from_url(REDIS_URL, decode_responses=True)
        await r.publish(CHANNEL, json.dumps(patch))
        await r.close()
    except Exception as e:
        print(f"Error publishing to Redis: {e}")


async def subscribe(callback):
    """
    Subscribe to state patches from Redis and invoke callback for each message.
    This is a blocking call that should run in a background task.
    """
    try:
        r = await aioredis.from_url(REDIS_URL, decode_responses=True)
        pubsub = r.pubsub()
        await pubsub.subscribe(CHANNEL)

        print(f"Subscribed to Redis channel: {CHANNEL}")

        async for msg in pubsub.listen():
            if msg["type"] == "message":
                try:
                    data = json.loads(msg["data"])
                    await callback(data)
                except json.JSONDecodeError as e:
                    print(f"Error decoding message: {e}")
                except Exception as e:
                    print(f"Error in callback: {e}")
    except Exception as e:
        print(f"Error subscribing to Redis: {e}")
        # Retry after delay
        await asyncio.sleep(5)
        await subscribe(callback)
