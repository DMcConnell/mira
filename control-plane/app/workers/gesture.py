import asyncio
import random
from ..models.core import Command
from ..core.arbiter import handle_command


GESTURES = ["idle", "palm", "swipe_left", "swipe_right", "fist"]


async def gesture_worker():
    """
    Simulates gesture detection device.
    In production, this would interface with actual gesture recognition hardware/software.
    Emits gesture commands every 3-5 seconds.
    """
    print("Gesture worker started")

    while True:
        try:
            # Random delay between gestures
            await asyncio.sleep(random.uniform(3, 5))

            # Pick random gesture (mostly idle, sometimes action)
            weights = [0.6, 0.1, 0.1, 0.1, 0.1]  # idle is more common
            g = random.choices(GESTURES, weights=weights)[0]

            cmd = Command(
                source="gesture",
                action=f"gesture_{g}",
                payload={"gesture": g, "confidence": random.uniform(0.7, 0.99)},
            )

            await handle_command(cmd)
            print(f"Gesture worker: emitted {g}")

        except Exception as e:
            print(f"Error in gesture worker: {e}")
            await asyncio.sleep(5)
