import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { AppRoute, PrivacyMode } from '../lib/types';
import { getVisibleApps, getAppName } from '../lib/appRegistry';

interface AppRailProps {
  gnArmed: boolean;
  currentApp: AppRoute;
  mode: PrivacyMode;
  onAppSelect: (app: AppRoute) => void;
}

export const AppRail: React.FC<AppRailProps> = ({
  gnArmed,
  currentApp,
  mode,
  onAppSelect,
}) => {
  const visibleApps = getVisibleApps(mode);

  // App icons (simple emoji for now, can be replaced with SVG icons)
  const appIcons: Record<AppRoute, string> = {
    home: '🏠',
    weather: '🌤️',
    email: '📧',
    finance: '💰',
    news: '📰',
    todos: '✅',
    calendar: '📅',
    settings: '⚙️',
  };

  return (
    <AnimatePresence>
      {gnArmed && (
        <motion.div
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -100, opacity: 0 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className='fixed top-0 left-0 right-0 z-50 bg-[#0a0a0f]/95 backdrop-blur-md border-b border-[#27272a]'
        >
          <div className='flex items-center justify-center gap-4 px-6 py-4'>
            {visibleApps.map((app) => {
              const isActive = app === currentApp;
              return (
                <button
                  key={app}
                  onClick={() => onAppSelect(app)}
                  className={`flex flex-col items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                    isActive
                      ? 'bg-[#6366f1] text-white'
                      : 'text-[#a1a1aa] hover:text-[#e4e4e7] hover:bg-[#18181b]'
                  }`}
                >
                  <span className='text-2xl'>{appIcons[app]}</span>
                  <span className='text-xs font-medium'>{getAppName(app)}</span>
                  {isActive && (
                    <motion.div
                      layoutId='activeIndicator'
                      className='absolute bottom-0 left-0 right-0 h-0.5 bg-[#6366f1]'
                    />
                  )}
                </button>
              );
            })}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default AppRail;


