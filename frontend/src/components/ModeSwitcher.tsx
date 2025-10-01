import React from 'react';

export type AppMode = 'morning' | 'ambient';

interface ModeSwitcherProps {
  mode: AppMode;
  onModeChange: (mode: AppMode) => void;
  className?: string;
}

export const ModeSwitcher: React.FC<ModeSwitcherProps> = ({
  mode,
  onModeChange,
  className = '',
}) => {
  return (
    <div
      className={`flex gap-1 bg-[#18181b] border border-[#27272a] rounded-lg p-1 ${className}`}
    >
      <button
        onClick={() => onModeChange('morning')}
        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
          mode === 'morning'
            ? 'bg-[#6366f1] text-white'
            : 'text-[#a1a1aa] hover:text-[#e4e4e7]'
        }`}
      >
        Morning
      </button>
      <button
        onClick={() => onModeChange('ambient')}
        className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
          mode === 'ambient'
            ? 'bg-[#6366f1] text-white'
            : 'text-[#a1a1aa] hover:text-[#e4e4e7]'
        }`}
      >
        Ambient
      </button>
    </div>
  );
};

export default ModeSwitcher;
