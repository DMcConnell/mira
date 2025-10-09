import axios from 'axios';
import type {
  MorningReport,
  Todo,
  Settings,
  VoiceInterpretRequest,
  VoiceInterpretResponse,
  HealthResponse,
} from './types';

// Get base URL from environment variable, default to localhost:8080
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

// Create axios instance with default config
const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Health endpoint
export const getHealth = async (): Promise<HealthResponse> => {
  const response = await api.get<HealthResponse>('/health');
  return response.data;
};

// Morning Report
export const getMorningReport = async (): Promise<MorningReport> => {
  const response = await api.get<MorningReport>('/api/v1/morning-report');
  return response.data;
};

// Todos
export const getTodos = async (): Promise<Todo[]> => {
  const response = await api.get<Todo[]>('/api/v1/todos');
  return response.data;
};

export const createTodo = async (text: string): Promise<Todo> => {
  const response = await api.post<Todo>('/api/v1/todos', { text });
  return response.data;
};

export const updateTodo = async (
  id: string,
  updates: Partial<Todo>,
): Promise<Todo> => {
  const response = await api.put<Todo>(`/api/v1/todos/${id}`, updates);
  return response.data;
};

export const deleteTodo = async (id: string): Promise<void> => {
  await api.delete(`/api/v1/todos/${id}`);
};

// Voice interpretation
export const interpretVoice = async (
  text: string,
): Promise<VoiceInterpretResponse> => {
  const response = await api.post<VoiceInterpretResponse>(
    '/api/v1/voice/interpret',
    { text } as VoiceInterpretRequest,
  );
  return response.data;
};

// Settings
export const getSettings = async (): Promise<Settings> => {
  const response = await api.get<Settings>('/api/v1/settings');
  return response.data;
};

export const updateSettings = async (settings: Settings): Promise<Settings> => {
  const response = await api.put<Settings>('/api/v1/settings', settings);
  return response.data;
};

// Vision snapshot URL (for img src)
export const getVisionSnapshotUrl = (): string => {
  return `${BASE_URL}/vision/snapshot.jpg`;
};

// WebSocket URL for vision
export const getVisionWebSocketUrl = (): string => {
  const wsProtocol = BASE_URL.startsWith('https') ? 'wss' : 'ws';
  const url = BASE_URL.replace(/^https?:\/\//, '');
  return `${wsProtocol}://${url}/ws/vision`;
};

// WebSocket URL for state updates
export const getStateWebSocketUrl = (): string => {
  const wsProtocol = BASE_URL.startsWith('https') ? 'wss' : 'ws';
  const url = BASE_URL.replace(/^https?:\/\//, '');
  return `${wsProtocol}://${url}/ws/state`;
};

// Command API - send commands to Control Plane
export const sendCommand = async (
  command: import('./types').Command,
): Promise<{ status: string; payload: unknown }> => {
  const response = await api.post('/api/v1/command', command);
  return response.data;
};

// State API - get current state snapshot
export const getState = async (): Promise<import('./types').AppState> => {
  const response = await api.get('/api/v1/state');
  return response.data;
};

export default api;
