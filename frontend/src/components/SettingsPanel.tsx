import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Settings, VisionIntent } from '../lib/types';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  settings: Settings | null;
  onSettingsChange: (settings: Settings) => Promise<void>;
  lastApiLatency: number | null;
  visionStatus: {
    connected: boolean;
    latestIntent: VisionIntent | null;
  };
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
  isOpen,
  onClose,
  settings,
  onSettingsChange,
  lastApiLatency,
  visionStatus,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === '.') {
        e.preventDefault();
        if (isOpen) {
          onClose();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleModeChange = async (
    mode: 'weatherMode' | 'newsMode',
    value: string,
  ) => {
    if (!settings) return;
    try {
      await onSettingsChange({
        ...settings,
        [mode]: value,
      });
    } catch (error) {
      console.error('Error updating settings:', error);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className='fixed inset-0 bg-black/60 backdrop-blur-sm z-40'
          />

          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className='fixed right-0 top-0 bottom-0 w-full max-w-md bg-[#0a0a0f] border-l border-[#27272a] z-50 overflow-y-auto'
          >
            <div className='p-6'>
              {/* Header */}
              <div className='flex justify-between items-center mb-8'>
                <h2 className='text-xl font-semibold text-[#fafafa]'>
                  Settings
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

              {/* App Info */}
              <section className='mb-6'>
                <h3 className='text-xs font-semibold text-[#71717a] uppercase tracking-wide mb-3'>
                  Application
                </h3>
                <div className='bg-[#111115] border border-[#27272a] rounded-lg p-4'>
                  <div className='space-y-3 text-sm'>
                    <div className='flex justify-between items-center'>
                      <span className='text-[#a1a1aa]'>Version</span>
                      <span className='text-[#e4e4e7] font-mono text-xs'>
                        {import.meta.env.VITE_APP_VERSION || '1.0.0'}
                      </span>
                    </div>
                    <div className='flex justify-between items-center'>
                      <span className='text-[#a1a1aa]'>API Latency</span>
                      <span className='text-[#e4e4e7] font-mono text-xs'>
                        {lastApiLatency !== null ? `${lastApiLatency}ms` : '—'}
                      </span>
                    </div>
                  </div>
                </div>
              </section>

              {/* Provider Settings */}
              {settings && (
                <section className='mb-6'>
                  <h3 className='text-xs font-semibold text-[#71717a] uppercase tracking-wide mb-3'>
                    Providers
                  </h3>
                  <div className='space-y-3'>
                    <div className='bg-[#111115] border border-[#27272a] rounded-lg p-4'>
                      <label className='block text-sm text-[#a1a1aa] mb-2'>
                        Weather
                      </label>
                      <select
                        value={settings.weatherMode}
                        onChange={(e) =>
                          handleModeChange('weatherMode', e.target.value)
                        }
                        className='w-full px-3 py-2 bg-[#18181b] text-[#e4e4e7] border border-[#27272a] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#6366f1] focus:border-transparent'
                      >
                        <option value='mock'>Mock</option>
                        <option value='live'>Live</option>
                      </select>
                    </div>

                    <div className='bg-[#111115] border border-[#27272a] rounded-lg p-4'>
                      <label className='block text-sm text-[#a1a1aa] mb-2'>
                        News
                      </label>
                      <select
                        value={settings.newsMode}
                        onChange={(e) =>
                          handleModeChange('newsMode', e.target.value)
                        }
                        className='w-full px-3 py-2 bg-[#18181b] text-[#e4e4e7] border border-[#27272a] rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#6366f1] focus:border-transparent'
                      >
                        <option value='mock'>Mock</option>
                        <option value='live'>Live</option>
                      </select>
                    </div>
                  </div>
                </section>
              )}

              {/* Vision Status */}
              <section className='mb-6'>
                <h3 className='text-xs font-semibold text-[#71717a] uppercase tracking-wide mb-3'>
                  Vision System
                </h3>
                <div className='bg-[#111115] border border-[#27272a] rounded-lg p-4'>
                  <div className='space-y-3 text-sm'>
                    <div className='flex justify-between items-center'>
                      <span className='text-[#a1a1aa]'>Status</span>
                      <span
                        className={`flex items-center gap-1.5 font-medium ${
                          visionStatus.connected
                            ? 'text-[#22c55e]'
                            : 'text-[#ef4444]'
                        }`}
                      >
                        <span className='w-1.5 h-1.5 rounded-full bg-current' />
                        {visionStatus.connected ? 'Connected' : 'Disconnected'}
                      </span>
                    </div>

                    {visionStatus.latestIntent && (
                      <>
                        <div className='flex justify-between items-center'>
                          <span className='text-[#a1a1aa]'>Gesture</span>
                          <span className='text-[#e4e4e7] font-medium'>
                            {visionStatus.latestIntent.gesture}
                          </span>
                        </div>
                        <div className='flex justify-between items-center'>
                          <span className='text-[#a1a1aa]'>Confidence</span>
                          <span className='text-[#e4e4e7]'>
                            {(
                              visionStatus.latestIntent.confidence * 100
                            ).toFixed(0)}
                            %
                          </span>
                        </div>
                        <div className='flex justify-between items-center'>
                          <span className='text-[#a1a1aa]'>Armed</span>
                          <span className='text-[#e4e4e7]'>
                            {visionStatus.latestIntent.armed ? 'Yes' : 'No'}
                          </span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </section>

              {/* Keyboard Shortcuts */}
              <section>
                <h3 className='text-xs font-semibold text-[#71717a] uppercase tracking-wide mb-3'>
                  Shortcuts
                </h3>
                <div className='bg-[#111115] border border-[#27272a] rounded-lg p-4'>
                  <div className='space-y-2.5 text-sm'>
                    <div className='flex justify-between items-center'>
                      <span className='text-[#a1a1aa]'>Toggle Settings</span>
                      <kbd className='px-2 py-1 bg-[#18181b] border border-[#27272a] text-[#a1a1aa] rounded text-xs font-mono'>
                        Ctrl + .
                      </kbd>
                    </div>
                    <div className='flex justify-between items-center'>
                      <span className='text-[#a1a1aa]'>Close</span>
                      <kbd className='px-2 py-1 bg-[#18181b] border border-[#27272a] text-[#a1a1aa] rounded text-xs font-mono'>
                        Esc
                      </kbd>
                    </div>
                  </div>
                </div>
              </section>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default SettingsPanel;
