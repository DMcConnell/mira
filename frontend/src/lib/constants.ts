// Mira MVP UI/UX Constants
// Compile-time only configuration

export const WAKE_KEYWORD = 'mira'; // regex word boundary, case-insensitive
export const DWELL_MS_DEFAULT = 700; // tuneable, default ON
export const GN_STEADY_MS = 250; // steady open hand duration for GN armed
export const GN_HYSTERESIS_MS = 120; // prevent flicker in GN armed state
export const PRIVACY_IDLE_TIMEOUT_MS = 300000; // 5 min

// Private code - default to 'unlock', should be set in .env as VITE_PRIVATE_CODE
export const PRIVATE_CODE = import.meta.env.VITE_PRIVATE_CODE || 'unlock';


