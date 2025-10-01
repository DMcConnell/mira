import React from 'react';
import Card from '../../components/Card';
import type { CalendarItem } from '../../lib/types';

interface CalendarPanelProps {
  items: CalendarItem[];
  loading?: boolean;
}

export const CalendarPanel: React.FC<CalendarPanelProps> = ({
  items,
  loading = false,
}) => {
  if (loading) {
    return (
      <Card title='Calendar' className='h-full'>
        <div className='space-y-3'>
          {[1, 2, 3].map((i) => (
            <div key={i} className='animate-pulse'>
              <div className='h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4 mb-2'></div>
              <div className='h-3 bg-gray-300 dark:bg-gray-600 rounded w-1/2'></div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card title='Calendar' className='h-full'>
      {items.length === 0 ? (
        <p className='text-gray-500 dark:text-gray-400'>No events scheduled</p>
      ) : (
        <div className='space-y-3'>
          {items.map((item) => (
            <div key={item.id} className='border-l-4 border-blue-500 pl-3'>
              <h4 className='font-medium'>{item.title}</h4>
              <p className='text-sm text-gray-600 dark:text-gray-400'>
                {new Date(item.startsAtISO).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
              {item.location && (
                <p className='text-xs text-gray-500 dark:text-gray-500'>
                  {item.location}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};

export default CalendarPanel;
