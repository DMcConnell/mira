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
              <div className='h-4 bg-[#27272a] rounded w-3/4 mb-2'></div>
              <div className='h-3 bg-[#27272a] rounded w-1/2'></div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card title='Calendar' className='h-full'>
      {items.length === 0 ? (
        <p className='text-[#71717a] text-sm'>No events scheduled</p>
      ) : (
        <div className='space-y-3'>
          {items.map((item) => (
            <div
              key={item.id}
              className='border-l-2 border-[#6366f1] pl-3 py-1'
            >
              <h4 className='font-medium text-[#e4e4e7] text-sm'>
                {item.title}
              </h4>
              <p className='text-xs text-[#a1a1aa] mt-0.5'>
                {new Date(item.startsAtISO).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
              {item.location && (
                <p className='text-xs text-[#71717a] mt-0.5'>{item.location}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};

export default CalendarPanel;
