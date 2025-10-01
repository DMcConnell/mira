import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models.app_wide import VisionIntent

router = APIRouter()

# Mock gestures to cycle through
MOCK_GESTURES = ["idle", "palm", "swipe_left", "swipe_right", "fist"]


@router.websocket("/ws/vision")
async def vision_websocket(websocket: WebSocket):
    """
    WebSocket endpoint that sends mock vision intents.
    Cycles through gestures every 2 seconds with varying confidence.
    """
    await websocket.accept()

    gesture_index = 0
    armed = False

    try:
        while True:
            # Get current gesture and cycle to next
            gesture = MOCK_GESTURES[gesture_index % len(MOCK_GESTURES)]
            gesture_index += 1

            # Determine if armed (palm gesture arms the system)
            if gesture == "palm":
                armed = True
            elif gesture == "idle":
                armed = False

            # Create mock vision intent
            intent = VisionIntent(
                tsISO=datetime.now(timezone.utc).isoformat(),
                gesture=gesture,
                confidence=0.85 if gesture != "idle" else 0.95,
                armed=armed,
            )

            # Send to client
            await websocket.send_json(intent.dict())

            # Wait 2 seconds before next update
            await asyncio.sleep(2)

    except WebSocketDisconnect:
        print("Vision WebSocket client disconnected")
    except Exception as e:
        print(f"Vision WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
