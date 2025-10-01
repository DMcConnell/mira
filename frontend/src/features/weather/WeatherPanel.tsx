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
          <div className='h-20 bg-[#27272a] rounded mb-3'></div>
          <div className='h-4 bg-[#27272a] rounded w-2/3'></div>
        </div>
      </Card>
    );
  }

  if (!weather) {
    return (
      <Card title='Weather' className='h-full'>
        <p className='text-[#71717a] text-sm'>Weather data unavailable</p>
      </Card>
    );
  }

  return (
    <Card title='Weather' className='h-full'>
      <div className='flex items-center gap-5'>
        <div className='text-6xl leading-none'>{weather.icon}</div>
        <div>
          <div className='text-4xl font-light text-[#fafafa] font-mono'>
            {Math.round(weather.tempC)}°
          </div>
          <div className='text-base text-[#a1a1aa] mt-1'>
            {weather.condition}
          </div>
        </div>
      </div>
      {weather.stale && (
        <div className='mt-4 text-xs text-[#fbbf24] bg-[#fbbf24]/10 border border-[#fbbf24]/20 px-3 py-2 rounded-lg'>
          ⚠️ Data may be stale
        </div>
      )}
      <div className='mt-4 text-xs text-[#52525b]'>
        Updated {new Date(weather.updatedISO).toLocaleTimeString()}
      </div>
    </Card>
  );
};

export default WeatherPanel;
