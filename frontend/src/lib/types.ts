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
  params?: Record<string, unknown>;
}

export interface HealthResponse {
  status: string;
  summary?: string;
}
