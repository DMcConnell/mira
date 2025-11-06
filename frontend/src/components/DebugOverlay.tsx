import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { SensorsState, UIState } from '../lib/types';
import { getVisibleApps } from '../lib/appRegistry';
import { getVisionWebSocketUrl, getVisionSnapshotUrl } from '../lib/api';
import type { VisionIntent } from '../lib/types';

interface DebugOverlayProps {
  enabled: boolean;
  uiState: UIState;
  sensorsState?: SensorsState;
  onClose: () => void;
}

export const DebugOverlay: React.FC<DebugOverlayProps> = ({
  enabled,
  uiState,
  sensorsState,
  onClose,
}) => {
  const [latestIntent, setLatestIntent] = useState<VisionIntent | null>(null);
  const [fps, setFps] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const lastUpdateRef = useRef<number>(Date.now());
  const imageRef = useRef<HTMLImageElement>(null);

  // Connect to vision WebSocket for gesture data
  useEffect(() => {
    if (!enabled) return;

    const ws = new WebSocket(getVisionWebSocketUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const intent: VisionIntent = JSON.parse(event.data);
        setLatestIntent(intent);

        const now = Date.now();
        const delta = now - lastUpdateRef.current;
        if (delta > 0) {
          setFps(Math.round(1000 / delta));
        }
        lastUpdateRef.current = now;
      } catch (error) {
        console.error('Failed to parse vision intent:', error);
      }
    };

    ws.onerror = () => {
      setIsConnected(false);
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [enabled]);

  // Refresh camera image periodically
  useEffect(() => {
    if (!enabled || !imageRef.current) return;

    const interval = setInterval(() => {
      if (imageRef.current) {
        // Force refresh by adding timestamp query param
        const baseUrl = getVisionSnapshotUrl();
        imageRef.current.src = `${baseUrl}?t=${Date.now()}`;
      }
    }, 100); // Update every 100ms (~10 FPS for snapshot)

    return () => clearInterval(interval);
  }, [enabled]);

  if (!enabled) {
    return null;
  }

  const visibleApps = getVisibleApps(uiState.mode);

  return (
    <AnimatePresence>
      {enabled && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className='fixed inset-0 bg-black/80 backdrop-blur-sm z-[100]'
          />

          {/* Overlay Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className='fixed right-0 top-0 bottom-0 w-full max-w-2xl bg-[#0a0a0f] border-l border-[#27272a] z-[101] overflow-y-auto'
          >
            <div className='p-6'>
              {/* Header */}
              <div className='flex justify-between items-center mb-6'>
                <h2 className='text-xl font-semibold text-[#fafafa]'>
                  Debug Overlay
                </h2>
                <button
                  onClick={onClose}
                  className='text-[#71717a] hover:text-[#e4e4e7] transition-colors p-1'
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
                      d='M6 18L18 6M6 6l12 12'
                    />
                  </svg>
                </button>
              </div>

              {/* Camera Preview */}
              <section className='mb-6'>
                <h3 className='text-xs font-semibold text-[#71717a] uppercase tracking-wide mb-3'>
                  Camera Preview
                </h3>
                <div className='bg-[#111115] border border-[#27272a] rounded-lg p-4'>
                  <div className='relative'>
                    <img
                      ref={imageRef}
                      src={`${getVisionSnapshotUrl()}?t=${Date.now()}`}
                      alt='Camera preview with landmarks'
                      className='w-full rounded-lg border border-[#27272a]'
                    />
                    <div className='absolute top-2 right-2 bg-black/70 text-white px-2 py-1 rounded text-xs font-mono'>
                      {fps} FPS
                    </div>
                    <div
                      className={`absolute top-2 left-2 px-2 py-1 rounded text-xs font-medium ${
                        isConnected
                          ? 'bg-[#22c55e]/20 text-[#22c55e] border border-[#22c55e]/30'
                          : 'bg-[#ef4444]/20 text-[#ef4444] border border-[#ef4444]/30'
                      }`}
                    >
                      <span className='inline-block w-1.5 h-1.5 rounded-full bg-current mr-1.5' />
                      {isConnected ? 'Live' : 'Offline'}
                    </div>
                    {latestIntent && (
                      <div className='absolute bottom-2 left-2 bg-black/70 text-white px-2 py-1 rounded text-xs'>
                        Gesture: {latestIntent.gesture} | GN Armed:{' '}
                        {latestIntent.armed ? 'Yes' : 'No'}
                      </div>
                    )}
                  </div>
                </div>
              </section>

              {/* Mode/State Panel */}
              <section className='mb-6'>
                <h3 className='text-xs font-semibold text-[#71717a] uppercase tracking-wide mb-3'>
                  Mode & State
                </h3>
                <div className='bg-[#111115] border border-[#27272a] rounded-lg p-4 space-y-2 text-sm'>
                  <div className='flex justify-between'>
                    <span className='text-[#a1a1aa]'>Privacy Mode</span>
                    <span className='text-[#e4e4e7] font-mono'>
                      {uiState.mode}
                    </span>
                  </div>
                  <div className='flex justify-between'>
                    <span className='text-[#a1a1aa]'>App Route</span>
                    <span className='text-[#e4e4e7] font-mono'>
                      {uiState.appRoute}
                    </span>
                  </div>
                  <div className='flex justify-between'>
                    <span className='text-[#a1a1aa]'>Focus Path</span>
                    <span className='text-[#e4e4e7] font-mono'>
                      {uiState.focusPath.join(' → ') || 'none'}
                    </span>
                  </div>
                  <div className='flex justify-between'>
                    <span className='text-[#a1a1aa]'>GN Armed</span>
                    <span
                      className={`font-mono ${
                        uiState.gnArmed ? 'text-[#22c55e]' : 'text-[#71717a]'
                      }`}
                    >
                      {uiState.gnArmed ? 'Yes' : 'No'}
                    </span>
                  </div>
                </div>
              </section>

              {/* Gesture Stream */}
              {sensorsState && (
                <section className='mb-6'>
                  <h3 className='text-xs font-semibold text-[#71717a] uppercase tracking-wide mb-3'>
                    Gesture Stream
                  </h3>
                  <div className='bg-[#111115] border border-[#27272a] rounded-lg p-4 space-y-3 text-sm'>
                    {Object.entries(sensorsState.hands).map(
                      ([handId, handData]) => (
                        <div key={handId} className='space-y-1'>
                          <div className='font-medium text-[#e4e4e7]'>
                            {handId} Hand
                          </div>
                          <div className='pl-4 space-y-1 text-xs'>
                            <div className='flex justify-between'>
                              <span className='text-[#71717a]'>Present</span>
                              <span className='text-[#e4e4e7]'>
                                {handData.present ? 'Yes' : 'No'}
                              </span>
                            </div>
                            <div className='flex justify-between'>
                              <span className='text-[#71717a]'>Pose</span>
                              <span className='text-[#e4e4e7] font-mono'>
                                {handData.pose}
                              </span>
                            </div>
                            <div className='flex justify-between'>
                              <span className='text-[#71717a]'>
                                Steady (ms)
                              </span>
                              <span className='text-[#e4e4e7] font-mono'>
                                {handData.steadyMs}
                              </span>
                            </div>
                            <div className='flex justify-between'>
                              <span className='text-[#71717a]'>Velocity</span>
                              <span className='text-[#e4e4e7] font-mono'>
                                {handData.velocity.mag.toFixed(3)}
                              </span>
                            </div>
                          </div>
                        </div>
                      ),
                    )}
                  </div>
                </section>
              )}

              {/* Privacy Banner */}
              <section className='mb-6'>
                <h3 className='text-xs font-semibold text-[#71717a] uppercase tracking-wide mb-3'>
                  Privacy Policy
                </h3>
                <div className='bg-[#111115] border border-[#27272a] rounded-lg p-4 space-y-2 text-sm'>
                  <div className='flex justify-between'>
                    <span className='text-[#a1a1aa]'>Current Mode</span>
                    <span className='text-[#e4e4e7] font-mono'>
                      {uiState.mode}
                    </span>
                  </div>
                  <div>
                    <span className='text-[#a1a1aa]'>Visible Apps:</span>
                    <div className='mt-2 flex flex-wrap gap-2'>
                      {visibleApps.map((app) => (
                        <span
                          key={app}
                          className='px-2 py-1 bg-[#18181b] border border-[#27272a] rounded text-xs font-mono text-[#e4e4e7]'
                        >
                          {app}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </section>

              {/* Voice Panel */}
              {sensorsState && sensorsState.voice && (
                <section className='mb-6'>
                  <h3 className='text-xs font-semibold text-[#71717a] uppercase tracking-wide mb-3'>
                    Voice
                  </h3>
                  <div className='bg-[#111115] border border-[#27272a] rounded-lg p-4 space-y-2 text-sm'>
                    <div className='flex justify-between'>
                      <span className='text-[#a1a1aa]'>Wake Detected</span>
                      <span className='text-[#e4e4e7]'>
                        {sensorsState.voice.heardWake ? 'Yes' : 'No'}
                      </span>
                    </div>
                    {sensorsState.voice.transcript && (
                      <div>
                        <span className='text-[#a1a1aa]'>Last Transcript:</span>
                        <div className='mt-1 text-[#e4e4e7] font-mono text-xs'>
                          {sensorsState.voice.transcript}
                        </div>
                      </div>
                    )}
                    {sensorsState.voice.intent && (
                      <div className='flex justify-between'>
                        <span className='text-[#a1a1aa]'>Last Intent</span>
                        <span className='text-[#e4e4e7] font-mono'>
                          {sensorsState.voice.intent}
                        </span>
                      </div>
                    )}
                    {sensorsState.voice.confidence !== undefined && (
                      <div className='flex justify-between'>
                        <span className='text-[#a1a1aa]'>Confidence</span>
                        <span className='text-[#e4e4e7] font-mono'>
                          {(sensorsState.voice.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                  </div>
                </section>
              )}

              {/* Timing Panel */}
              {sensorsState && sensorsState.perf && (
                <section>
                  <h3 className='text-xs font-semibold text-[#71717a] uppercase tracking-wide mb-3'>
                    Performance
                  </h3>
                  <div className='bg-[#111115] border border-[#27272a] rounded-lg p-4 space-y-2 text-sm'>
                    <div className='flex justify-between'>
                      <span className='text-[#a1a1aa]'>FPS</span>
                      <span className='text-[#e4e4e7] font-mono'>
                        {sensorsState.perf.fps}
                      </span>
                    </div>
                    <div className='flex justify-between'>
                      <span className='text-[#a1a1aa]'>Reducer Latency</span>
                      <span className='text-[#e4e4e7] font-mono'>
                        {sensorsState.perf.latencies.reducerMs}ms
                      </span>
                    </div>
                    <div className='flex justify-between'>
                      <span className='text-[#a1a1aa]'>WS Latency</span>
                      <span className='text-[#e4e4e7] font-mono'>
                        {sensorsState.perf.latencies.wsMs}ms
                      </span>
                    </div>
                  </div>
                </section>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default DebugOverlay;
