"""
Mira MVP UI/UX Constants
Compile-time only configuration
"""

# Gesture constants
GN_STEADY_MS = 250  # steady open hand duration for GN armed
GN_HYSTERESIS_MS = 120  # prevent flicker in GN armed state
DWELL_MS_DEFAULT = 700  # dwell time for focus selection

# Privacy constants
PRIVACY_IDLE_TIMEOUT_MS = 300000  # 5 min

# Wake keyword (for reference - actual processing happens in backend)
WAKE_KEYWORD = "mira"


