import React from 'react';
import Card from '../../components/Card';
import type { WeatherSnapshot } from '../../lib/types';

interface WeatherPanelProps {
  weather: WeatherSnapshot | null;
  loading?: boolean;
}

export const WeatherPanel: React.FC<WeatherPanelProps> = ({
  weather,
  loading = false,
}) => {
  if (loading) {
    return (
      <Card title='Weather' className='h-full'>
        <div className='animate-pulse'>
          <div className='h-16 bg-gray-300 dark:bg-gray-600 rounded mb-3'></div>
          <div className='h-4 bg-gray-300 dark:bg-gray-600 rounded w-2/3'></div>
        </div>
      </Card>
    );
  }

  if (!weather) {
    return (
      <Card title='Weather' className='h-full'>
        <p className='text-gray-500 dark:text-gray-400'>
          Weather data unavailable
        </p>
      </Card>
    );
  }

  return (
    <Card title='Weather' className='h-full'>
      <div className='flex items-center gap-4'>
        <div className='text-5xl'>{weather.icon}</div>
        <div>
          <div className='text-4xl font-bold'>
            {Math.round(weather.tempC)}°C
          </div>
          <div className='text-lg text-gray-600 dark:text-gray-400'>
            {weather.condition}
          </div>
        </div>
      </div>
      {weather.stale && (
        <div className='mt-3 text-sm text-yellow-600 dark:text-yellow-500'>
          ⚠️ Data may be stale
        </div>
      )}
      <div className='mt-2 text-xs text-gray-500 dark:text-gray-500'>
        Updated: {new Date(weather.updatedISO).toLocaleTimeString()}
      </div>
    </Card>
  );
};

export default WeatherPanel;
