"""
Hand tracking module - tracks individual hand state, pose, velocity, and steady time.
"""

from collections import deque
from typing import Deque, Dict, Tuple

import numpy as np


class HandTracker:
    """Tracks individual hand state: pose, velocity, steadyMs"""

    def __init__(self):
        self.pose = "unknown"
        self.pose_start_time = 0.0
        self.last_centroid = (0.0, 0.0)
        self.velocity_history: Deque[Tuple[float, float, float]] = deque(
            maxlen=5
        )  # (time, x, y)

    def update_pose(self, new_pose: str, current_time: float):
        """Update pose and track steady time"""
        if new_pose != self.pose:
            self.pose = new_pose
            self.pose_start_time = current_time

    def get_steady_ms(self, current_time: float) -> int:
        """Get how long the hand has been in current pose (ms)"""
        if self.pose_start_time == 0:
            return 0
        return int((current_time - self.pose_start_time) * 1000)

    def update_velocity(self, centroid: Tuple[float, float], current_time: float):
        """Update velocity based on centroid movement"""
        if self.last_centroid == (0.0, 0.0):
            self.last_centroid = centroid
            return

        dt = current_time - (
            self.velocity_history[-1][0] if self.velocity_history else current_time
        )
        if dt > 0:
            dx = centroid[0] - self.last_centroid[0]
            dy = centroid[1] - self.last_centroid[1]
            vx = dx / dt if dt > 0 else 0.0
            vy = dy / dt if dt > 0 else 0.0

            self.velocity_history.append((current_time, vx, vy))
            self.last_centroid = centroid

    def get_velocity(self) -> Dict[str, float]:
        """Get current velocity (x, y, magnitude)"""
        if not self.velocity_history:
            return {"x": 0.0, "y": 0.0, "mag": 0.0}

        # Use most recent velocity
        _, vx, vy = self.velocity_history[-1]
        mag = np.sqrt(vx * vx + vy * vy)
        return {"x": float(vx), "y": float(vy), "mag": float(mag)}

