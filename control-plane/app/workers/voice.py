import asyncio
import random
from ..models.core import Command
from ..core.arbiter import handle_command


VOICE_COMMANDS = [
    ("add_todo", {"text": "Buy groceries"}),
    ("add_todo", {"text": "Call dentist"}),
    ("add_todo", {"text": "Review pull requests"}),
    ("toggle_mic", {}),
    ("toggle_cam", {}),
    ("set_mode", {"mode": "voice"}),
    ("set_mode", {"mode": "idle"}),
]


async def voice_worker():
    """
    Simulates voice command detection device.
    In production, this would interface with hotword detection and speech-to-text.
    Emits voice commands every 8-15 seconds.
    """
    print("Voice worker started")

    while True:
        try:
            # Random delay between voice commands
            await asyncio.sleep(random.uniform(8, 15))

            # Pick random voice command
            action, payload = random.choice(VOICE_COMMANDS)

            cmd = Command(source="voice", action=action, payload=payload)

            await handle_command(cmd)
            print(f"Voice worker: emitted {action}")

        except Exception as e:
            print(f"Error in voice worker: {e}")
            await asyncio.sleep(5)
