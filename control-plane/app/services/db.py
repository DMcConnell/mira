import aiosqlite
import os

DB_PATH = "data/control_plane.db"


async def init_db():
    """
    Initialize SQLite database with events and snapshots tables.
    Events store all command outcomes for audit/replay.
    Snapshots store periodic full state for efficient recovery.
    """
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(
            """
        CREATE TABLE IF NOT EXISTS events (
          id TEXT PRIMARY KEY,
          ts TEXT NOT NULL,
          commandId TEXT NOT NULL,
          type TEXT NOT NULL,
          payload TEXT NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS snapshots (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts TEXT NOT NULL,
          state TEXT NOT NULL
        );
        
        CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
        CREATE INDEX IF NOT EXISTS idx_events_commandId ON events(commandId);
        CREATE INDEX IF NOT EXISTS idx_snapshots_ts ON snapshots(ts);
        """
        )
        await db.commit()
