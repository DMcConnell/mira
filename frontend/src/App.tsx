import { useState, useEffect, useCallback, useRef } from 'react';
import './App.css';
import { CalendarPanel } from './features/calendar';
import { WeatherPanel } from './features/weather';
import { NewsPanel } from './features/news';
import { TodosPanel } from './features/todos';
import { VisionPanel } from './features/vision';
import {
  ModeSwitcher,
  Toast,
  TextCommandModal,
  SettingsPanel,
  LoginModal,
  type AppMode,
  type ToastType,
} from './components';
import { authService } from './lib/auth';
import type {
  MorningReport,
  Todo,
  Settings,
  VisionIntent,
  StatePatch,
  AppState,
} from './lib/types';
import {
  getMorningReport,
  createTodo,
  updateTodo,
  deleteTodo,
  interpretVoice,
  getSettings,
  updateSettings as updateSettingsApi,
  getVisionWebSocketUrl,
  getStateWebSocketUrl,
  getState,
} from './lib/api';

interface ToastState {
  message: string;
  type: ToastType;
  isVisible: boolean;
}

function App() {
  const [mode, setMode] = useState<AppMode>('morning');
  const [morningReport, setMorningReport] = useState<MorningReport | null>(
    null,
  );
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Authentication state
  const [isAuthenticated, setIsAuthenticated] = useState(
    authService.isAuthenticated(),
  );
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(
    !authService.isAuthenticated(),
  );

  // Modal/Panel states
  const [isCommandModalOpen, setIsCommandModalOpen] = useState(false);
  const [isSettingsPanelOpen, setIsSettingsPanelOpen] = useState(false);

  // Toast state
  const [toast, setToast] = useState<ToastState>({
    message: '',
    type: 'info',
    isVisible: false,
  });

  // Settings state
  const [settings, setSettings] = useState<Settings | null>(null);

  // API latency tracking
  const [lastApiLatency, setLastApiLatency] = useState<number | null>(null);

  // Vision WebSocket state
  const [visionStatus, setVisionStatus] = useState<{
    connected: boolean;
    latestIntent: VisionIntent | null;
  }>({
    connected: false,
    latestIntent: null,
  });
  const wsRef = useRef<WebSocket | null>(null);

  // Control Plane state WebSocket
  const [controlPlaneStatus, setControlPlaneStatus] = useState<{
    connected: boolean;
    lastUpdate: string | null;
  }>({
    connected: false,
    lastUpdate: null,
  });
  const stateWsRef = useRef<WebSocket | null>(null);
  // State tracking - will be used in future phases
  const [appState, setAppState] = useState<AppState | null>(null);

  // Show toast helper
  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    setToast({ message, type, isVisible: true });
  }, []);

  // Hide toast
  const hideToast = useCallback(() => {
    setToast((prev) => ({ ...prev, isVisible: false }));
  }, []);

  // Fetch morning report data
  const fetchMorningReport = useCallback(async () => {
    try {
      console.log('appState', appState);
      setLoading(true);
      setError(null);
      const startTime = Date.now();
      const data = await getMorningReport();
      const latency = Date.now() - startTime;
      setLastApiLatency(latency);
      setMorningReport(data);
      setTodos(data.todos);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to fetch morning report',
      );
      console.error('Error fetching morning report:', err);
      showToast('Failed to fetch data', 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  // Fetch settings
  const fetchSettings = useCallback(async () => {
    try {
      const data = await getSettings();
      setSettings(data);
    } catch (err) {
      console.error('Error fetching settings:', err);
    }
  }, []);

  // Update settings
  const handleUpdateSettings = useCallback(
    async (newSettings: Settings) => {
      try {
        const updated = await updateSettingsApi(newSettings);
        setSettings(updated);
        showToast('Settings updated', 'success');
      } catch (err) {
        console.error('Error updating settings:', err);
        showToast('Failed to update settings', 'error');
      }
    },
    [showToast],
  );

  // Handle authentication required event
  useEffect(() => {
    const handleAuthRequired = () => {
      setIsAuthenticated(false);
      setIsLoginModalOpen(true);
    };

    window.addEventListener('auth:required', handleAuthRequired);
    return () =>
      window.removeEventListener('auth:required', handleAuthRequired);
  }, []);

  // Handle successful login
  const handleLoginSuccess = useCallback(() => {
    setIsAuthenticated(true);
    setIsLoginModalOpen(false);
    showToast('Successfully authenticated', 'success');
    // Fetch data after successful login
    fetchMorningReport();
    fetchSettings();
  }, [fetchMorningReport, fetchSettings, showToast]);

  // Initial data fetch (only if authenticated)
  useEffect(() => {
    if (isAuthenticated) {
      fetchMorningReport();
      fetchSettings();
    }
  }, [isAuthenticated, fetchMorningReport, fetchSettings]);

  // Fetch initial state from Control Plane (only if authenticated)
  useEffect(() => {
    if (!isAuthenticated) return;

    const fetchInitialState = async () => {
      try {
        const state = await getState();
        setAppState(state);
        console.log('Initial state loaded:', state);
      } catch (err) {
        console.error('Failed to fetch initial state:', err);
      }
    };
    fetchInitialState();
  }, [isAuthenticated]);

  // Apply state patch to current state
  const applyStatePatch = useCallback(
    (patch: StatePatch) => {
      console.log('Applying state patch:', patch);

      setControlPlaneStatus((prev) => ({
        ...prev,
        lastUpdate: patch.ts,
      }));

      // Simple path-based state updates
      // For now, just handle a few common patterns
      if (patch.path === '/mode') {
        setMode(patch.value as AppMode);
        showToast(`Mode switched to ${patch.value}`, 'info');
      } else if (patch.path === '/todos/+') {
        // Add new todo
        const newTodo = patch.value as Todo;
        setTodos((prev) => [...prev, newTodo]);
        showToast('Todo added via Control Plane', 'success');
      } else if (patch.path.startsWith('/todos/')) {
        // Update specific todo (not implemented in this phase)
        console.log('Todo update:', patch);
      } else if (patch.path === '/gesture') {
        // Update gesture state
        setAppState((prev) => ({ ...prev, gesture: patch.value as string }));
      }

      // Update the full app state
      setAppState((prev) => {
        const newState = { ...prev };
        // Simple path handling for now
        const pathParts = patch.path.split('/').filter((p) => p);
        if (pathParts.length === 1) {
          newState[pathParts[0]] = patch.value;
        }
        return newState;
      });
    },
    [showToast],
  );

  // Setup Vision WebSocket (only if authenticated)
  useEffect(() => {
    if (!isAuthenticated) return;

    const connectWebSocket = () => {
      try {
        const ws = new WebSocket(getVisionWebSocketUrl());
        wsRef.current = ws;

        ws.onopen = () => {
          setVisionStatus((prev) => ({ ...prev, connected: true }));
          console.log('Vision WebSocket connected');
        };

        ws.onmessage = (event) => {
          try {
            const intent: VisionIntent = JSON.parse(event.data);
            setVisionStatus({ connected: true, latestIntent: intent });
          } catch (error) {
            console.error('Failed to parse vision intent:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('Vision WebSocket error:', error);
        };

        ws.onclose = () => {
          setVisionStatus((prev) => ({ ...prev, connected: false }));
          console.log('Vision WebSocket disconnected');
          // Attempt to reconnect after 5 seconds
          setTimeout(connectWebSocket, 5000);
        };
      } catch (error) {
        console.error('Failed to connect WebSocket:', error);
        setTimeout(connectWebSocket, 5000);
      }
    };

    connectWebSocket();

    return () => {
      wsRef.current?.close();
    };
  }, [isAuthenticated]);

  // Setup State WebSocket (Control Plane, only if authenticated)
  useEffect(() => {
    if (!isAuthenticated) return;

    const connectStateWebSocket = () => {
      try {
        const ws = new WebSocket(getStateWebSocketUrl());
        stateWsRef.current = ws;

        ws.onopen = () => {
          setControlPlaneStatus((prev) => ({ ...prev, connected: true }));
          console.log('Control Plane WebSocket connected');
        };

        ws.onmessage = (event) => {
          try {
            const patch: StatePatch = JSON.parse(event.data);
            applyStatePatch(patch);
          } catch (error) {
            console.error('Failed to parse state patch:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('Control Plane WebSocket error:', error);
        };

        ws.onclose = () => {
          setControlPlaneStatus((prev) => ({ ...prev, connected: false }));
          console.log('Control Plane WebSocket disconnected');
          // Attempt to reconnect after 5 seconds
          setTimeout(connectStateWebSocket, 5000);
        };
      } catch (error) {
        console.error('Failed to connect State WebSocket:', error);
        setTimeout(connectStateWebSocket, 5000);
      }
    };

    connectStateWebSocket();

    return () => {
      stateWsRef.current?.close();
    };
  }, [isAuthenticated, applyStatePatch]);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+. or Cmd+. to toggle settings
      if ((e.ctrlKey || e.metaKey) && e.key === '.') {
        e.preventDefault();
        setIsSettingsPanelOpen((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Todo handlers with optimistic updates
  const handleAddTodo = async (text: string) => {
    const optimisticTodo: Todo = {
      id: `temp-${Date.now()}`,
      text,
      done: false,
      createdAtISO: new Date().toISOString(),
    };
    setTodos((prev) => [...prev, optimisticTodo]);

    try {
      const newTodo = await createTodo(text);
      setTodos((prev) =>
        prev.map((t) => (t.id === optimisticTodo.id ? newTodo : t)),
      );
      showToast('Todo added', 'success');
    } catch (err) {
      setTodos((prev) => prev.filter((t) => t.id !== optimisticTodo.id));
      console.error('Error creating todo:', err);
      showToast('Failed to add todo', 'error');
      throw err;
    }
  };

  const handleToggleTodo = async (id: string, done: boolean) => {
    const previousTodos = [...todos];
    setTodos((prev) => prev.map((t) => (t.id === id ? { ...t, done } : t)));

    try {
      await updateTodo(id, { done });
    } catch (err) {
      setTodos(previousTodos);
      console.error('Error updating todo:', err);
      showToast('Failed to update todo', 'error');
      throw err;
    }
  };

  const handleDeleteTodo = async (id: string) => {
    const previousTodos = [...todos];
    setTodos((prev) => prev.filter((t) => t.id !== id));

    try {
      await deleteTodo(id);
      showToast('Todo deleted', 'success');
    } catch (err) {
      setTodos(previousTodos);
      console.error('Error deleting todo:', err);
      showToast('Failed to delete todo', 'error');
      throw err;
    }
  };

  // Handle voice command
  const handleVoiceCommand = async (text: string) => {
    try {
      const result = await interpretVoice(text);
      console.log('Voice interpretation result:', result);

      // Handle different intents
      if (result.intent === 'switch_mode') {
        const targetMode = result.params?.mode as AppMode;
        if (targetMode === 'morning' || targetMode === 'ambient') {
          setMode(targetMode);
          showToast(`Switched to ${targetMode} mode`, 'success');
        }
      } else if (result.intent === 'add_todo') {
        const todoText = result.params?.text as string;
        if (todoText) {
          await handleAddTodo(todoText);
        }
      } else if (result.intent === 'unknown') {
        showToast('Command not recognized', 'error');
      } else {
        showToast(`Command processed: ${result.intent}`, 'success');
      }
    } catch (err) {
      console.error('Error interpreting command:', err);
      showToast('Failed to process command', 'error');
    }
  };

  return (
    <div className='app-container'>
      <header className='app-header'>
        <h1 className='app-title'>Mira</h1>
        <div className='header-controls'>
          <ModeSwitcher mode={mode} onModeChange={setMode} />
          <button
            onClick={() => setIsCommandModalOpen(true)}
            className='command-button'
            title='Open voice command (or press Ctrl+K)'
          >
            <svg
              className='w-5 h-5'
              fill='none'
              stroke='currentColor'
              viewBox='0 0 24 24'
            >
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z'
              />
            </svg>
          </button>
          <button
            onClick={() => setIsSettingsPanelOpen(true)}
            className='settings-button'
            title='Open settings (or press Ctrl+.)'
          >
            <svg
              className='w-5 h-5'
              fill='none'
              stroke='currentColor'
              viewBox='0 0 24 24'
            >
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z'
              />
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M15 12a3 3 0 11-6 0 3 3 0 016 0z'
              />
            </svg>
          </button>
        </div>
      </header>

      {error && (
        <div className='error-banner'>
          <span>⚠️ {error}</span>
          <button onClick={fetchMorningReport} className='retry-button'>
            Retry
          </button>
        </div>
      )}

      <main className='app-main'>
        {mode === 'morning' ? (
          <div className='grid-layout'>
            <div className='grid-item'>
              <CalendarPanel
                items={morningReport?.calendar || []}
                loading={loading}
              />
            </div>
            <div className='grid-item'>
              <WeatherPanel
                weather={morningReport?.weather || null}
                loading={loading}
              />
            </div>
            <div className='grid-item'>
              <NewsPanel items={morningReport?.news || []} loading={loading} />
            </div>
            <div className='grid-item'>
              <TodosPanel
                todos={todos}
                loading={loading}
                onAdd={handleAddTodo}
                onToggle={handleToggleTodo}
                onDelete={handleDeleteTodo}
              />
            </div>
            <div className='grid-item vision-grid-item'>
              <VisionPanel showPreview={true} compact={false} />
            </div>
          </div>
        ) : (
          <div className='ambient-mode'>
            <div className='time-display'>
              {new Date().toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </div>
            <div className='date-display'>
              {new Date().toLocaleDateString([], {
                weekday: 'long',
                month: 'long',
                day: 'numeric',
              })}
            </div>
            {morningReport?.weather && (
              <div className='ambient-weather'>
                <span className='ambient-weather-icon'>
                  {morningReport.weather.icon}
                </span>
                <span className='ambient-weather-temp'>
                  {Math.round(morningReport.weather.tempC)}°C
                </span>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Modals & Panels */}
      <TextCommandModal
        isOpen={isCommandModalOpen}
        onClose={() => setIsCommandModalOpen(false)}
        onSubmit={handleVoiceCommand}
      />

      <SettingsPanel
        isOpen={isSettingsPanelOpen}
        onClose={() => setIsSettingsPanelOpen(false)}
        settings={settings}
        onSettingsChange={handleUpdateSettings}
        lastApiLatency={lastApiLatency}
        visionStatus={visionStatus}
        controlPlaneStatus={controlPlaneStatus}
      />

      {/* Login Modal */}
      <LoginModal isOpen={isLoginModalOpen} onSuccess={handleLoginSuccess} />

      {/* Toast Notifications */}
      <Toast
        message={toast.message}
        type={toast.type}
        isVisible={toast.isVisible}
        onClose={hideToast}
      />
    </div>
  );
}

export default App;
