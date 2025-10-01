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
    <div className={`flex gap-2 ${className}`}>
      <button
        onClick={() => onModeChange('morning')}
        className={`px-4 py-2 rounded-md transition-colors ${
          mode === 'morning'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
        }`}
      >
        Morning
      </button>
      <button
        onClick={() => onModeChange('ambient')}
        className={`px-4 py-2 rounded-md transition-colors ${
          mode === 'ambient'
            ? 'bg-blue-600 text-white'
            : 'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
        }`}
      >
        Ambient
      </button>
    </div>
  );
};

export default ModeSwitcher;
