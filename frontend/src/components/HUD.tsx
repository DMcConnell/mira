import React from 'react';
import type { PrivacyMode } from '../lib/types';

interface HUDProps {
  mode: PrivacyMode;
  micOn: boolean;
  camOn: boolean;
  wsConnected: boolean;
  debugEnabled: boolean;
  wake: boolean;
}

export const HUD: React.FC<HUDProps> = ({
  mode,
  micOn,
  camOn,
  wsConnected,
  debugEnabled,
  wake,
}) => {
  return (
    <div className='fixed top-4 right-4 z-50 flex flex-col gap-2'>
      {/* Privacy Chip */}
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium ${
          mode === 'private'
            ? 'bg-[#fbbf24]/20 text-[#fbbf24] border border-[#fbbf24]/30'
            : 'bg-[#27272a] text-[#a1a1aa] border border-[#3f3f46]'
        }`}
      >
        {mode === 'private' ? (
          <svg
            className='w-4 h-4'
            fill='currentColor'
            viewBox='0 0 20 20'
          >
            <path
              fillRule='evenodd'
              d='M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z'
              clipRule='evenodd'
            />
          </svg>
        ) : (
          <svg
            className='w-4 h-4'
            fill='none'
            stroke='currentColor'
            viewBox='0 0 24 24'
          >
            <path
              strokeLinecap='round'
              strokeLinejoin='round'
              strokeWidth={2}
              d='M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z'
            />
          </svg>
        )}
        <span>{mode === 'private' ? 'Private' : 'Public'}</span>
      </div>

      {/* Mic Chip */}
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium ${
          micOn
            ? 'bg-[#22c55e]/20 text-[#22c55e] border border-[#22c55e]/30'
            : 'bg-[#ef4444]/20 text-[#ef4444] border border-[#ef4444]/30'
        }`}
      >
        <span className='w-1.5 h-1.5 rounded-full bg-current' />
        <span>Mic</span>
      </div>

      {/* Cam Chip */}
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium ${
          camOn
            ? 'bg-[#22c55e]/20 text-[#22c55e] border border-[#22c55e]/30'
            : 'bg-[#ef4444]/20 text-[#ef4444] border border-[#ef4444]/30'
        }`}
      >
        <span className='w-1.5 h-1.5 rounded-full bg-current' />
        <span>Cam</span>
      </div>

      {/* WebSocket Chip */}
      <div
        className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium ${
          wsConnected
            ? 'bg-[#22c55e]/20 text-[#22c55e] border border-[#22c55e]/30'
            : 'bg-[#ef4444]/20 text-[#ef4444] border border-[#ef4444]/30'
        }`}
      >
        <span className='w-1.5 h-1.5 rounded-full bg-current' />
        <span>WS</span>
      </div>

      {/* Debug Chip */}
      {debugEnabled && (
        <div className='flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#6366f1]/20 text-[#6366f1] border border-[#6366f1]/30'>
          <span className='w-1.5 h-1.5 rounded-full bg-current' />
          <span>Debug</span>
        </div>
      )}

      {/* Wake Chip */}
      {wake && (
        <div className='flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#f59e0b]/20 text-[#f59e0b] border border-[#f59e0b]/30'>
          <span className='w-1.5 h-1.5 rounded-full bg-current animate-pulse' />
          <span>Wake</span>
        </div>
      )}
    </div>
  );
};

export default HUD;


