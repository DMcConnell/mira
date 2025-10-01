import React from 'react';
import Card from '../../components/Card';
import type { NewsItem } from '../../lib/types';

interface NewsPanelProps {
  items: NewsItem[];
  loading?: boolean;
}

export const NewsPanel: React.FC<NewsPanelProps> = ({
  items,
  loading = false,
}) => {
  if (loading) {
    return (
      <Card title='News' className='h-full'>
        <div className='space-y-3'>
          {[1, 2, 3].map((i) => (
            <div key={i} className='animate-pulse'>
              <div className='h-4 bg-[#27272a] rounded w-full mb-2'></div>
              <div className='h-3 bg-[#27272a] rounded w-1/3'></div>
            </div>
          ))}
        </div>
      </Card>
    );
  }

  return (
    <Card title='News' className='h-full'>
      {items.length === 0 ? (
        <p className='text-[#71717a] text-sm'>No news available</p>
      ) : (
        <div className='space-y-2 max-h-80 overflow-y-auto'>
          {items.map((item) => (
            <a
              key={item.id}
              href={item.url}
              target='_blank'
              rel='noopener noreferrer'
              className='block hover:bg-[#18181b] p-3 -mx-1 rounded-lg transition-colors'
            >
              <h4 className='font-medium text-sm leading-snug text-[#e4e4e7] mb-1.5'>
                {item.title}
              </h4>
              <div className='flex justify-between items-center text-xs text-[#71717a]'>
                <span>{item.source}</span>
                <span>{new Date(item.publishedISO).toLocaleDateString()}</span>
              </div>
            </a>
          ))}
        </div>
      )}
    </Card>
  );
};

export default NewsPanel;
