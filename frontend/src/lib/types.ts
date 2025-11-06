// TypeScript types matching backend Pydantic models

export interface CalendarItem {
  id: string;
  title: string;
  startsAtISO: string;
  endsAtISO: string;
  location?: string;
}

export interface WeatherSnapshot {
  updatedISO: string;
  tempC: number;
  condition: string;
  icon: string;
  stale?: boolean;
}

export interface NewsItem {
  id: string;
  title: string;
  source: string;
  url: string;
  publishedISO: string;
}

export interface Todo {
  id: string;
  text: string;
  done: boolean;
  createdAtISO: string;
}

export interface MorningReport {
  calendar: CalendarItem[];
  weather: WeatherSnapshot;
  news: NewsItem[];
  todos: Todo[];
}

export interface VisionIntent {
  tsISO: string;
  gesture: string;
  confidence: number;
  armed: boolean;
}

export interface Settings {
  weatherMode: string;
  newsMode: string;
}

export interface VoiceInterpretRequest {
  text: string;
}

export interface VoiceInterpretResponse {
  intent: string;
  confidence: number;
  action: string;
  parameters: Record<string, unknown>;
  params?: Record<string, unknown>; // Legacy alias
}

export interface HealthResponse {
  status: string;
  summary?: string;
}

export interface Command {
  id?: string;
  ts?: string;
  source: 'voice' | 'gesture' | 'system';
  action: string;
  payload?: Record<string, unknown>;
}

export interface StatePatch {
  ts: string;
  path: string;
  value: unknown;
}

export interface AppState {
  mode?: string;
  todos?: Todo[];
  gesture?: string;
  [key: string]: unknown;
}

// UI State types for Phase A & B
export type PrivacyMode = 'public' | 'private';
export type AppRoute =
  | 'home'
  | 'weather'
  | 'email'
  | 'finance'
  | 'news'
  | 'todos'
  | 'calendar'
  | 'settings';

export interface UIState {
  mode: PrivacyMode;
  appRoute: AppRoute;
  focusPath: string[];
  gnArmed: boolean;
  debug: {
    enabled: boolean;
  };
  hud: {
    micOn: boolean;
    camOn: boolean;
    wsConnected: boolean;
    wake: boolean;
  };
  confirm?: {
    text: string;
    action: Command;
    expiresAt: number;
  };
}

export interface SensorsState {
  hands: Record<
    string,
    {
      present: boolean;
      pose: 'open' | 'fist' | 'pinch' | 'twoFinger' | 'unknown';
      velocity: { x: number; y: number; mag: number };
      steadyMs: number;
    }
  >;
  voice: {
    heardWake: boolean;
    intent?: string;
    transcript?: string;
    confidence?: number;
  };
  perf: {
    fps: number;
    latencies: { reducerMs: number; wsMs: number };
  };
}
